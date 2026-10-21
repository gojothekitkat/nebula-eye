$ErrorActionPreference = "Stop"

Write-Host "NEBULA EYE - dependency setup" -ForegroundColor Cyan

py -3.13 --version
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.13 was not found. Install Python 3.13 and try again."
}

py -3.13 -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Could not upgrade pip."
}

py -3.13 -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed."
}

Write-Host ""
Write-Host "Setup complete. Start the app with:" -ForegroundColor Green
Write-Host "py -3.13 nebula_eye.py" -ForegroundColor Yellow
