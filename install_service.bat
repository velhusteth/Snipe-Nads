@echo off
echo Monad Sniper Bot Service Installer
echo ================================

:: Check for admin privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
) else (
    echo Please run this script as Administrator!
    pause
    exit /b 1
)

:: Create directories
echo Creating directories...
if not exist "C:\MonadBot" mkdir "C:\MonadBot"
if not exist "C:\MonadBot\logs" mkdir "C:\MonadBot\logs"

:: Copy files
echo Copying files...
xcopy /s /y "%~dp0*" "C:\MonadBot\"

:: Create virtual environment if it doesn't exist
if not exist "C:\MonadBot\venv" (
    echo Creating virtual environment...
    python -m venv "C:\MonadBot\venv"
)

:: Activate virtual environment and install requirements
echo Installing requirements...
call "C:\MonadBot\venv\Scripts\activate.bat"
pip install -r "C:\MonadBot\requirements.txt"

:: Install the service
echo Installing Windows service...
"C:\MonadBot\venv\Scripts\python.exe" "C:\MonadBot\windows_service.py" install

echo.
echo Installation complete! You can now:
echo 1. Start the service from Windows Services
echo 2. Or use these commands:
echo    - net start MonadSniper
echo    - net stop MonadSniper
echo    - net restart MonadSniper
echo.
echo To uninstall: "C:\MonadBot\venv\Scripts\python.exe" "C:\MonadBot\windows_service.py" remove
echo.
pause 