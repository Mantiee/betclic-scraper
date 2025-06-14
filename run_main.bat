@echo off
REM ----------------------------------------
REM Runs main.py in this directory
REM ----------------------------------------

REM Change to the script’s directory (so it works even when double-clicked)
cd /d "%~dp0"

REM Run the Python script
python main.py

REM Pause so you can see any output or errors
pause
