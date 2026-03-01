# 🛡️ PSAI (Private SQL AI)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-AI-green)
![Chainlit](https://img.shields.io/badge/Chainlit-UI-purple)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-orange)

An AI-powered local SQL architect that uses **Retrieval-Augmented Generation (RAG)** to understand enterprise database schemas and converts natural language into executable SQL queries safely using local LLMs. 

This application guarantees 100% privacy by running entirely on your local machine using **Ollama**, but also supports cloud models like **OpenAI's GPT-4o-mini** for high-performance query generation.

---

## ✨ Features

- **🗣️ Natural Language to SQL**: Ask questions in plain English, and the application generates complex SQL queries tailored to your schema.
- **📚 RAG-Powered Context**: Uses local Vector Databases (Qdrant) to index enterprise PDF schemas so the LLM knows the exact tables and columns to query.
- **🔒 100% Privacy Option**: Run open-source models offline via **Ollama** (e.g., `qwen2.5-coder:7b`) with zero data leaving your machine.
- **⚡ Hot-Swappable AI Models**: Switch between Local LLMs and OpenAI seamlessly from the UI without restarting the server.
- **📊 Safe Local Execution**: Generated SQL queries are safely executed against a local SQLite database (`demo.db`) using Pandas DataFrames to prevent cursor mismanagement.
- **🧠 Intent Routing**: The system automatically detects whether you want to chat casually or generate a database query.

---

## 🏗️ Architecture Stack

* **Frontend**: [Chainlit](https://docs.chainlit.io/) (Asynchronous Chat UI)
* **Orchestration**: [LangChain](https://python.langchain.com/) (Chains, Prompts, Output Parsers)
* **LLM Engine**: [Ollama](https://ollama.com/) (Local) / OpenAI (Cloud)
* **Embeddings**: Local Ollama Embeddings
* **Vector Store**: Qdrant (Persistent Local Storage)
* **Database Execution**: SQLite3 + Pandas

---

## 📂 Project Structure

```text
private_sql/
├── core/                   # The central brain of the application
│   ├── config/             # Hardcoded path configurations
│   └── llm/                # Prompts and LangChain execution logic (chains)
├── data/                   # The persistence layer
│   ├── databases/          # Actual target SQL databases (e.g., demo.db)
│   ├── documents/          # Raw PDF schemas (e.g., Enterprise Schema PDF)
│   └── vector_db/          # Qdrant vector database persistence
├── interfaces/             # Frontend layer
│   └── ui/                 # Chainlit Web Server (app.py)
├── modules/                # Functional AI/Execution engines
│   ├── database/           # Local SQlite execution engine
│   └── retrieval/          # RAG vectorization and document splitting
├── .env                    # Environment variables (OpenAI Keys)
├── ARCHITECTURE.md         # Detailed code architecture explanation
├── HOW_TO_RUN.md           # Step-by-step launch instructions
└── run.bat                 # Windows batch script for quick start
```

---

## 🚀 Getting Started

### 1. Prerequisites

Ensure you have the following installed on your machine:
* Python 3.10+
* [Ollama](https://ollama.com/) (If running locally)

### 2. Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/parthibanktech/private-sql-architect.git
cd private-sql-architect
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Variables (Optional)

If you plan to use OpenAI instead of the local Ollama models, configure your `.env` file in the root directory:

```env
OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_GOES_HERE
```

---

## 🎮 How to Run

### Method 1: Using the Batch Script (Windows)
Simply double-click the `run.bat` file in the root directory.

### Method 2: Command Line
1. Open a terminal in the root directory.
2. Run the Chainlit application:
```bash
.\venv\Scripts\python.exe -m chainlit run interfaces\ui\app.py -w
```
3. Open your browser and navigate to **[http://localhost:8000](http://localhost:8000)**.

---

## ⚙️ Configuration & Usage

Once the UI is running, click the **⚙️ Settings Slider Icon** near the chat box to configure the agent.

* **Option A: Local Ollama (100% Privacy)**
  1. Ensure you have the model downloaded: `ollama pull qwen2.5-coder:7b`
  2. Select `Qwen 2.5 Coder 7B` from the AI Model Power dropdown.
  3. Hit **Confirm**.

* **Option B: OpenAI (ChatGPT)**
  1. Ensure your `.env` file has a valid OpenAI key.
  2. Select `OpenAI GPT-4o-Mini` from the AI Model Power dropdown.
  3. Hit **Confirm**.

To test the system, try asking a natural language business question such as: *"Show me the total sales by region for the last quarter."* (Refer to `testing_queries.md` for more examples).

---

## ☁️ Deployment (Render.com)

This repository is configured for automated Docker deployments to Render. 

1. Create an account at [Render.com](https://render.com/).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub account and select the `private-sql-architect` repository.
4. Render will automatically detect the `Dockerfile`.
5. Under settings, scroll down to **Deploy Hook URL** and copy it.
6. Go to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.
7. Name the secret `RENDER_DEPLOY_HOOK_URL` and paste the URL from Render.
8. Every push to the `main` branch will now automatically trigger a GitHub Action to test the code and deploy the latest Docker container to Render!
