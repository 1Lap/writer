@echo off
echo ============================================================
echo Building LMU Telemetry Logger Executable
echo ============================================================
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build executable
echo.
echo Building with PyInstaller...
pyinstaller --onefile ^
    --name "LMU_Telemetry_Logger" ^
    --icon=NONE ^
    --add-data "src;src" ^
    --hidden-import psutil ^
    --hidden-import datetime ^
    --collect-all src ^
    example_app.py

echo.
echo ============================================================
echo Build Complete!
echo.
echo Executable location: dist\LMU_Telemetry_Logger.exe
echo ============================================================
pause
