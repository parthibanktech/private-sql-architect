import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore 
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.config.config import PERSIST_DIR, DOC_DIR, EMBEDDING_MODEL

def setup_rag_pipeline(force_manuals=False):
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    collection_name = "schema_docs"

    try:
        # Step 1: Check if already indexed (INSTANT LOAD)
        # Skip cache if force_manuals is True (Advanced Mode)
        if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR) and not force_manuals:
            print("⚡ [ARCHITECT] Knowledge Base exists. Bypassing Heavy Computations.")
            vectorstore = QdrantVectorStore.from_existing_collection(
                embedding=embeddings,
                path=PERSIST_DIR,
                collection_name=collection_name,
            )
            return vectorstore.as_retriever(search_kwargs={"k": 10}), "Success (Loaded from cache)"
    except Exception as e:
        print(f"⚠️ [LOCK WARNING] Persistent DB locked: {e}. Falling back to In-Memory mode.")

    # Step 2: Adaptive Indexing
    documents = []
    if not os.path.exists(DOC_DIR):
        return None, "Documents directory not found."

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    
    # Priority 1: The V7 Final PDF (Always Index)
    schema_pdf = os.path.join(DOC_DIR, "Enterprise_Master_Schema_v7_FINAL.pdf")
    if os.path.exists(schema_pdf):
        print("📖 [CORE] Indexing Enterprise Master Schema...")
        loader = PyPDFLoader(schema_pdf)
        loaded_docs = loader.load()
        for doc in loaded_docs:
            doc.metadata["dialect"] = "ALL" # Shared across all modes
        documents.extend(text_splitter.split_documents(loaded_docs))

    # Priority 2: Manuals (Only if forced or small environment)
    if force_manuals:
        print("📚 [ADVANCED] Indexing Heavy SQL Manuals (This may take minutes on GTX 1650)...")
        manual_files = [f for f in os.listdir(DOC_DIR) if "Official" in f and f.endswith(".pdf")]
        for manual in manual_files:
            loader = PyPDFLoader(os.path.join(DOC_DIR, manual))
            loaded_docs = loader.load()
            
            # Metadata Tagging for Dialect Isolation
            tag = "Oracle" if "Oracle" in manual else "PostgreSQL"
            print(f"🏷️  Tagging {manual} as '{tag}'")
            for doc in loaded_docs:
                doc.metadata["dialect"] = tag
                
            documents.extend(text_splitter.split_documents(loaded_docs))

    if not documents:
        return None, "No core schema found."

    print(f"🧠 [VECTOR ENGINE] Embedding {len(documents)} chunks...")
    try:
        # Try persistent first
        vectorstore = QdrantVectorStore.from_documents(
            documents,
            embeddings,
            path=PERSIST_DIR,
            collection_name=collection_name,
            force_recreate=True
        )
        status = "Success (Index Complete)"
    except Exception:
        # Fallback to In-Memory
        print("🛡️ [FAIL-SAFE] Using In-Memory Vector Store to avoid file lock.")
        vectorstore = QdrantVectorStore.from_documents(
            documents,
            embeddings,
            location=":memory:", # FULLY IN-MEMORY
            collection_name=collection_name,
        )
        status = "Success (In-Memory Fail-Safe Active)"
    
    return vectorstore.as_retriever(search_kwargs={"k": 10}), status
