$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not found. Run .\setup_windows.ps1 first." -ForegroundColor Yellow
    exit 1
}

& .\.venv\Scripts\Activate.ps1
python -m streamlit run app.py

