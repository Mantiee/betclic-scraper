@echo off
REM ----------------------------------------
REM Runs test_the_db.py in this directory
REM ----------------------------------------

REM Change to the batch file’s directory
cd /d "%~dp0"

REM Execute the test script
python test_the_db.py

REM Keep the console open to view output
pause
