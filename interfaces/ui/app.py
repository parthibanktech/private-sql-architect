import chainlit as cl
import chainlit.input_widget as iw
import re
import os
from dotenv import load_dotenv

load_dotenv()

# Provide a default JWT secret for cloud deployments where .env is missing
os.environ.setdefault("CHAINLIT_AUTH_SECRET", "uE1n6Xb-7O-65Q81e4Yt0sB3I57LzT2i9c6=")


from modules.retrieval.rag import setup_rag_pipeline
from core.llm.chains import update_chain
from modules.database.database import execute_sql

# --- Global Vector Store ---
GLOBAL_RETRIEVER = None

# --- Authentication Module ---
@cl.password_auth_callback
async def auth_callback(username, password):
    # Dummy sign-up / login: Accepts any non-empty username & password
    if username and password:
        return cl.User(identifier=username)
    return None

@cl.on_chat_start
async def on_chat_start():
    global GLOBAL_RETRIEVER
    # Set AI Avatar
    try:
        await cl.Avatar(name="PSAI (Private SQL AI)", path="public/logo.png").send()
    except Exception:
        pass


    welcome_msg = """
# 🕵️‍♂️ PSAI (Private SQL AI)
**Premium AI Data Assistant** | **Local & Secure**

---

### 🚀 Immediate Instructions:
1. **⚙️ Enable Connection**: Open settings slider and connect to your preferred AI Model and Database Dialect.
2. **💬 Chat using Natural Language**: You can now ask queries about your selected database natively. 
"""
    await cl.Message(content=welcome_msg).send()
    cl.user_session.set("memory", [])
    default_model_str = os.environ.get("DEFAULT_AI_MODEL", "qwen2.5-coder:7b")
    initial_model_idx = 2 # Default to 7B
    if default_model_str == "gpt-4o-mini":
        initial_model_idx = 4
    
    settings = await cl.ChatSettings(
        [
            iw.Select(
                id="dialect",
                label="Target Database Dialect",
                values=["SQLite (Local Demo)", "PostgreSQL", "Oracle"],
                initial_index=0,
            ),
            iw.Select(
                id="kb_mode",
                label="Knowledge Base Mode",
                values=[
                    "🛡️ Standard Blueprint (Schema Only - High Accuracy)",
                    "📚 Advanced Multi-Dialect (Includes Oracle/Postgres Manuals)"
                ],
                initial_index=0,
            ),
            iw.Select(
                id="model",
                label="AI Model Power",
                values=[
                    "Qwen 2.5 Coder 1.5B (⚡ Fast)", 
                    "Qwen 2.5 Coder 3B (🌟 Recommended for 4GB VRAM)",
                    "Qwen 2.5 Coder 7B (⚖️ High Quality / Slow on 1650)", 
                    "Qwen 2.5 Coder 32B (🧠 Ultra / 24GB VRAM)",
                    "OpenAI GPT-4o-Mini (☁️ Cloud / Requires API Key)"
                ],
                initial_index=initial_model_idx, 
            )
        ]
    ).send()

    try:
        async with cl.Step("🔧 Setting up RAG Engine...") as step:
            if GLOBAL_RETRIEVER is None:
                retriever, status = await cl.make_async(setup_rag_pipeline)()
                if retriever is None:
                    await cl.Message(content=f"❌ **Setup Failed:** {status}").send()
                    return
                GLOBAL_RETRIEVER = retriever
            
            cl.user_session.set("retriever", GLOBAL_RETRIEVER)

        async with cl.Step("🧠 Tuning High-Level Model (7B)...") as step:
            await update_chain(dialect="SQLite", model="qwen2.5-coder:7b", kb_mode="Standard") 
        
        await cl.Message(content="✅ **System Ready!** Documentation is now persistent and indexed for maximum speed.").send()

    except Exception as e:
        await cl.Message(content=f"❌ **Critical Setup Error:** {str(e)}").send()

@cl.on_settings_update
async def setup_agent(settings):
    dialect_selection = settings["dialect"]
    dialect_map = {
        "SQLite (Local Demo)": "SQLite",
        "PostgreSQL": "PostgreSQL",
        "Oracle": "Oracle"
    }
    target_dialect = dialect_map.get(dialect_selection, "SQLite")
    
    kb_selection = settings["kb_mode"]
    kb_mode = "Advanced" if "Advanced" in kb_selection else "Standard"

    # Re-trigger RAG setup if Advanced mode is picked and manuals aren't indexed
    if kb_mode == "Advanced":
        async with cl.Step("📚 Indexing SQL Manuals for Advanced Mode...") as step:
            retriever, status = await cl.make_async(setup_rag_pipeline)(force_manuals=True)
            cl.user_session.set("retriever", retriever)

    model_selection = settings["model"]
    model_map = {
        "Qwen 2.5 Coder 1.5B (⚡ Fast)": "qwen2.5-coder:1.5b",
        "Qwen 2.5 Coder 3B (🌟 Recommended for 4GB VRAM)": "qwen2.5-coder:3b",
        "Qwen 2.5 Coder 7B (⚖️ High Quality / Slow on 1650)": "qwen2.5-coder:7b",
        "Qwen 2.5 Coder 32B (🧠 Ultra / 24GB VRAM)": "qwen2.5-coder:32b",
        "OpenAI GPT-4o-Mini (☁️ Cloud / Requires API Key)": "gpt-4o-mini"
    }
    target_model = model_map.get(model_selection, "qwen2.5-coder:7b")

    if target_model != "gpt-4o-mini":
        import asyncio
        async with cl.Step(f"📥 Ensuring local model '{target_model}' is installed (this may take a moment)...") as step:
            proc = await asyncio.create_subprocess_shell(
                f"ollama pull {target_model}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            if proc.returncode == 0:
                step.output = f"✅ Model '{target_model}' is downloaded and ready to use!"
            else:
                step.output = f"⚠️ Warning: Check your internet connection or Ollama installation."

    await update_chain(dialect=target_dialect, model=target_model, kb_mode=kb_mode)
    
    # CRITICAL: Clear memory on dialect/settings switch to prevent "Dialect Poisoning"
    cl.user_session.set("memory", [])
    
    await cl.Message(content=f"""
🔄 **Settings Updated:**
- **Mode**: `{kb_mode}`
- **Dialect**: `{target_dialect}`
- **Model**: `{target_model}`
*Context reset to prevent mixed results.*
""").send()

@cl.on_message
async def on_message(message: cl.Message):
    chain = cl.user_session.get("rag_chain")
    memory = cl.user_session.get("memory") # List of (Role, Content) tuples
    dialect = cl.user_session.get("current_dialect")
    
    if not chain:
        await cl.Message(content="⚠️ **Initializing...** Please wait for 'System Ready'.").send()
        return

    # Format History for Prompt
    history_str = "\n".join([f"{role}: {text}" for role, text in memory[-25:]]) # Keep last 25 turns

    response_text = ""
    msg = cl.Message(content="")
    
    try:
        # 1. Routing Decision (Inside Step)
        async with cl.Step("🧠 PSAI is thinking...") as step:
            step.input = message.content
            
            intent_chain = cl.user_session.get("intent_chain")
            intent_raw = await intent_chain.ainvoke({"question": message.content, "history": history_str})
            intent = intent_raw.strip().replace("'", "").replace(".", "").replace('\"', "")
            
            step.output = f"Routing to: {intent}"
            
        # 2. Main Response Streaming (Outside Step for full visibility)
        if "Conversational" in intent:
            chat_chain = cl.user_session.get("chat_chain")
            async for chunk in chat_chain.astream({"question": message.content, "history": history_str}):
                response_text += chunk
                await msg.stream_token(chunk)
        else:
            # Use Technical SQL Chain (RAG)
            async for chunk in chain.astream({"question": message.content, "history": history_str}):
                response_text += chunk
                await msg.stream_token(chunk)
        
        await msg.send()
        
        # Update Memory
        memory.append(("User", message.content))
        memory.append(("AI", response_text))
        
        cl.user_session.set("memory", memory)

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
             await cl.Message(content=f"❌ **Model Missing:**\nYou selected a model that is not installed on this machine.\nPlease run `ollama pull [model_name]` in the terminal first.\nDetails: `{error_msg}`").send()
        else:
            await cl.Message(content=f"❌ **Model Error:** `{error_msg}`").send()
        return

    # Search for SQL code blocks
    sql_match = re.search(r"```(?:sql|oracle|postgresql|sqlite)?\n?(.+?)\n?```", response_text, re.DOTALL | re.IGNORECASE)
    if sql_match:
        sql_query = sql_match.group(1).strip()
        # Basic validation to ensure it's not a generic code block
        if "SELECT" in sql_query.upper() or "WITH" in sql_query.upper():
            if dialect == "SQLite":
                actions = [cl.Action(name="run_query", payload={"sql": sql_query}, label="▶️ Run on Demo DB")]
                await cl.Message(content="Would you like to execute this query locally?", actions=actions).send()
            else:
                await cl.Message(content=f"ℹ️ **Dialect Insight:** This query was generated specifically for **{dialect}**. Note that execution is currently only enabled for the local **SQLite Demo DB**.").send()

@cl.action_callback("run_query")
async def on_action_run(action: cl.Action):
    sql_query = action.payload["sql"]
    
    async with cl.Step("📊 Executing Query...") as step:
        step.input = sql_query
        df, error = await cl.make_async(execute_sql)(sql_query)
        
        if error:
            await cl.Message(content=f"❌ **Error executing SQL:**\n`{error}`").send()
            return

        if df.empty:
            await cl.Message(content="⚠️ **Query returned no results.**").send()
            return

        # Handle Large Datasets properly
        row_count = len(df)
        if row_count > 20:
            display_df = df.head(20)
            note = f"\n\n*Note: Showing first 20 rows out of {row_count} total.*"
        else:
            display_df = df
            note = ""

        # Create CSV for download
        csv_data = df.to_csv(index=False).encode("utf-8")
        elements = [
            cl.File(name="query_results.csv", content=csv_data, display="inline")
        ]

        await cl.Message(
            content=f"✨ **Execution Results ({row_count} rows):**\n\n{display_df.to_markdown(index=False)}{note}",
            elements=elements
        ).send()
