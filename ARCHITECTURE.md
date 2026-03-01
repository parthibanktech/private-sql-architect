# 📖 Extensive Code Architecture & Step-by-Step Analysis

This document provides an exhaustive, step-by-step breakdown of **Uday's Private SQL Architect**. It is intended for code review and comprehensive submission evaluation. It explains every module, every folder, the exact flow of data, and how the entire system executes a user request from start to finish.

---

## 📂 Part 1: Comprehensive Directory Structure Breakdown

The codebase follows a strict modular design pattern to separate the frontend interface, the core AI logic, data retrieval (RAG), and the backend database execution.

* **`core/`**: The central brain of the application. Handles all AI routing, logic, configurations, and instruction sets.
  * `config/config.py`: Hardcoded path configurations and model choices.
  * `llm/prompts.py`: The system prompts that instruct the LLM on how to behave, how to detect intent, and how to write SQL.
  * `llm/chains.py`: The Langchain logic. It chains the LLMs, the Retrievers, and the Prompts together into execution pipelines.
* **`interfaces/`**: The frontend layer.
  * `ui/app.py`: The Main Chainlit Web Server. This file handles all the asyncio web-hooks for chat interface events.
* **`modules/`**: The underlying functional engines.
  * `retrieval/rag.py`: The Retrieval-Augmented Generation (RAG) engine. Responsible for indexing PDFs and saving them to the vector database.
  * `database/database.py`: The execution engine. Responsible for safely querying the generated SQL against the actual `demo.db` SQLite file securely.
* **`data/`**: The persistence layer.
  * `documents/`: Stores the raw PDF schemas (e.g., `Enterprise_Master_Schema_v7_FINAL.pdf`).
  * `vector_db/`: The persistent Qdrant vector database (so the app doesn't have to re-read the PDF on every single reboot).
  * `databases/`: Stores the actual target SQL databases (like `demo.db`).

*(Note on `__init__.py`)*: Every sub-folder contains an empty `__init__.py` file. **These are strictly required by the Python compiler.** They explicitly declare the directory as a formal Python Module, allowing cross-file imports like `from core.llm.chains import update_chain`. Without them, the app will crash with a `ModuleNotFoundError`.

---

## 💻 Part 2: Code-Level Execution Lifecycle

What exactly happens at the code level when you run the application and send a message? Here is the granular coding execution breakdown.

### Step 2.1: Server Initialization (`interfaces/ui/app.py`)
Chainlit detects the browser and invokes the asynchronous start event.
```python
@cl.on_chat_start
async def on_chat_start():
    # 1. Renders Settings Combo-boxes (SQLite, OpenAI, Qwen defaults)
    settings = await cl.ChatSettings([...]).send()
    
    # 2. Asynchronously boots the RAG vector engine
    async with cl.Step("🔧 Setting up RAG Engine...") as step:
        retriever, status = await cl.make_async(setup_rag_pipeline)()
    
    # 3. Chains the LLM pipelines
    await update_chain(dialect="SQLite", model="qwen2.5-coder:7b", kb_mode="Standard")
```

### Step 2.2: RAG Vector Engine Boots (`modules/retrieval/rag.py`)
The pipeline reads your Enterprise PDF using Langchain Document Loaders.
```python
def setup_rag_pipeline(force_manuals=False):
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    # Splitting logic preserves 200 character overlap so context isn't lost across pages
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    
    schema_pdf = os.path.join(DOC_DIR, "Enterprise_Master_Schema_v7_FINAL.pdf")
    loader = PyPDFLoader(schema_pdf)
    documents.extend(text_splitter.split_documents(loader.load()))
    
    # Computes numerical embeddings and saves them strictly to the persistent disk path
    vectorstore = QdrantVectorStore.from_documents(documents, embeddings, path=PERSIST_DIR)
    
    # Returns the retriever object allowing Top-K similarity matching
    return vectorstore.as_retriever(search_kwargs={"k": 10}), "Success"
```

### Step 2.3: Message Intent Routing (`core/llm/chains.py` & `prompts.py`)
When you type a message, the `intent_chain` decides if you want a SQL query or just a generic conversation.
```python
# The Prompt explicitly forces the LLM to output ONLY "Conversational" or "SQL_Generation"
ROUTE_PROMPT = """You are an intelligent intent router... reply with ONLY one word..."""

# The Chain hooks the String output parser to the LLM
intent_chain = (
    PromptTemplate.from_template(ROUTE_PROMPT)
    | llm
    | StrOutputParser()
)
```

In `app.py`:
```python
intent_raw = await intent_chain.ainvoke({"question": message.content, "history": history_str})
if "Conversational" in intent:
    # Streams normal chat response
else:
    # Routes to heavy database vector RAG logic
```

### Step 2.4: RAG Retrieval & SQL Generation (`core/llm/chains.py`)
If intent is SQL_Generation, the `rag_chain` takes over.
```python
if retriever:
    rag_chain = (
        # itemgetter("question") isolates the raw string so Pydantic doesn't throw Validation crashes!
        {
          "context": itemgetter("question") | retriever | format_docs, 
          "question": itemgetter("question"), 
          "history": itemgetter("history")
        }
        | qa_prompt # "You are an expert SQL Architect..."
        | llm       # The Ollama or OpenAI Engine
        | StrOutputParser() # Extracts raw markdown string
    )
```

### Step 2.5: Local Execution Validation (`modules/database/database.py`)
Once the SQL is generated, `app.py` scans for Markdown tags using Regex. It passes the raw sql string natively into Pandas for safe, DataFrame-powered execution against the local SQLite Demo file.
```python
import pandas as pd
import sqlite3

def execute_sql(query):
    # Connects purely to the local dummy database
    db_path = "data/databases/demo.db" 
    try:
        conn = sqlite3.connect(db_path)
        # Using Pandas to read SQL protects against raw cursor mismanagement
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)
```

### Step 2.6: Dynamic Hot-Swapping Models (`interfaces/ui/app.py`)
If the user touches the Combo-Box on the UI, it fires this webhook.
```python
@cl.on_settings_update
async def setup_agent(settings):
    target_model = model_map.get(settings["model"], "qwen2.5-coder:7b")
    
    # If using local Ollama, asynchronous shells ensure the model automatically downloads
    # if it doesn't exist, preventing 404 Model Missing crashes.
    if target_model != "gpt-4o-mini":
        proc = await asyncio.create_subprocess_shell(f"ollama pull {target_model}")
        await proc.communicate()
        
    await update_chain(dialect=settings["dialect"], model=target_model, kb_mode=settings["kb_mode"])
    
    # IMPORTANT: Flushes Context Memory instantly to prevent "Dialect Poisoning" across models
    cl.user_session.set("memory", []) 
```
