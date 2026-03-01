@echo off
echo ===================================================
echo 🚀 PSAI (Private SQL AI) - Launcher
echo ===================================================
echo.
echo Please select the AI Engine you want to run:
echo.
echo [1] Local Ollama (100%% Private, Requires qwen2.5-coder:7b installed)
echo [2] OpenAI ChatGPT (Requires OPENAI_API_KEY in .env file)
echo.
set /p engine_choice="Enter 1 or 2: "

if "%engine_choice%"=="1" (
    echo.
    echo 🛡️ Starting with Local Ollama...
    echo 📥 Ensuring Qwen 7B model is installed ^(this may take a moment if not downloaded^)...
    ollama pull qwen2.5-coder:7b
    set DEFAULT_AI_MODEL=qwen2.5-coder:7b
) else if "%engine_choice%"=="2" (
    echo.
    echo ☁️ Starting with OpenAI ChatGPT...
    @REM You can set an environment variable here if you want your python code to read it and default to OpenAI!
    set DEFAULT_AI_MODEL=gpt-4o-mini
) else (
    echo Invalid choice. Starting with default settings...
)

echo.
echo ⏳ Launching Web Interface...
.\venv\Scripts\python.exe -m chainlit run interfaces\ui\app.py -w
