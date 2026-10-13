@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo M365 Assurance is not set up yet.
    echo Open PowerShell in this folder and run: .\setup_windows.ps1
    pause
    exit /b 1
)

echo Starting M365 Assurance...
".venv\Scripts\python.exe" -m streamlit run app.py
