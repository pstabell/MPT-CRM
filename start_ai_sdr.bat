@echo off
REM AI SDR Phase 2 Integration Startup Script
REM Double-click this file to start the integration server

cd /d "%~dp0"

echo.
echo ============================================================
echo 🤖 AI SDR PHASE 2 - CRM DISCOVERY INTEGRATION
echo ============================================================
echo.
echo Starting up integration server...
echo Mission Control Card: 60ba5b82-db74-4d9c-b99f-6f6f22173908
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python first.
    echo.
    pause
    exit /b 1
)

REM Run the startup script
echo 🚀 Launching AI SDR Integration...
echo.
python start_ai_sdr_integration.py

echo.
echo Integration server stopped.
pause