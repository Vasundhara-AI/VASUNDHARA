@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo [ERROR] Virtual environment Python not found at "%PYTHON%".
    echo Create/activate your venv first, then retry.
    exit /b 1
)

echo [INFO] Ensuring PyInstaller is installed...
"%PYTHON%" -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    "%PYTHON%" -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        exit /b 1
    )
)

echo [INFO] Building Windows exe...
"%PYTHON%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --name windows-ai-assistant ^
  --onedir ^
  --windowed ^
  --collect-all whisper ^
  --collect-all tiktoken ^
  --collect-all llama_cpp ^
  --hidden-import pyttsx3.drivers.sapi5 ^
  assistant.py

if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

if exist ".env" (
    copy /Y ".env" "dist\windows-ai-assistant\.env" >nul
)

if /I "%~1"=="--with-models" (
    if exist "models" (
        echo [INFO] Copying models folder into dist output...
        xcopy /E /I /Y "models" "dist\windows-ai-assistant\models" >nul
    )
)

echo [OK] Build complete.
echo Output exe: dist\windows-ai-assistant\windows-ai-assistant.exe
echo.
echo Tip:
echo   - Use "build.bat --with-models" to package local model files into dist.
echo   - Without that flag, keep your models folder next to the exe folder.

endlocal
