# 🚀 How to Run PSAI (Private SQL AI)

This guide will walk you through exactly how to start the application and configure it to run using either **Local Ollama Models** (100% Private) or **OpenAI (ChatGPT)**.

---

## Step 1: Start the Application

To launch the web interface, open a terminal in VS Code, ensure you are in the `d:\AI\private_sql` directory, and run this command:

```powershell
.\venv\Scripts\python.exe -m chainlit run interfaces\ui\app.py -w
```

Once the terminal says it's running, open your web browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## Step 2: Choose Your AI Engine

On the Chainlit interface (`http://localhost:8000`), look at the bottom of the screen near the chat input box. Click the **⚙️ Settings Slider Icon** to open the configuration panel. Under the **"AI Model Power"** dropdown, select your preferred engine:

### Option A: Using Local Ollama (100% Privacy 🛡️)

This option requires zero API keys and never sends your data to the cloud.

1. **Prerequisite**: First, make sure you have the selected model downloaded to your machine. Open a *new* terminal window and pull the recommended model:
   ```powershell
   ollama pull qwen2.5-coder:7b
   ```
2. **Select in UI**: Once the download completes, go to the Chainlit Settings panel and select `Qwen 2.5 Coder 7B`.
3. Hit **Confirm** and start chatting!

### Option B: Using OpenAI (ChatGPT ☁️)

This is the fastest and smartest option, but requires an active internet connection and an OpenAI API key.

1. **Setup API Key**: Open the `.env` file located in the root of your project (`d:\AI\private_sql\.env`).
2. Replace the placeholder text with your actual secret key:
   ```env
   OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_GOES_HERE
   ```
   *Save the file.* (The Chainlit app will automatically detect the save and reload).
3. **Select in UI**: Go to the Chainlit Settings panel and select `OpenAI GPT-4o-Mini`.
4. Hit **Confirm** and start chatting!

---

## Step 3: Test the System

If you need queries to test the RAG engine or SQL generation, open the **`testing_queries.md`** file in this project and copy-paste any of the Natural Language business questions into the chat box!
