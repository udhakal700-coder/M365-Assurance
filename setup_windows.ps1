$ErrorActionPreference = "Stop"

Write-Host "Setting up M365 Assurance..." -ForegroundColor Cyan

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    $VenvCreated = $false

    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3.12 -c "import sys; print(sys.version)" 2>$null

        if ($LASTEXITCODE -eq 0) {
            py -3.12 -m venv .venv
            $VenvCreated = $true
        }
    }

    if (-not $VenvCreated -and (Get-Command python -ErrorAction SilentlyContinue)) {
        python -m venv .venv
        $VenvCreated = $true
    }

    if (-not $VenvCreated) {
        throw "Python was not found. Install Python 3.12 or newer, then reopen PowerShell."
    }
}

& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "Running automated tests..." -ForegroundColor Cyan
python -m pytest -q

Write-Host "Setup complete. Run: python -m streamlit run app.py" -ForegroundColor Green
