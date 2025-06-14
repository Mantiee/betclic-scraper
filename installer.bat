@echo off
REM ----------------------------------------
REM Installer for Betclic scraper dependencies
REM ----------------------------------------

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install required packages
echo Installing required Python packages...
pip install undetected-chromedriver selenium pywin32

echo.
echo All done! You can now run your script with:
echo     python your_script_name.py
echo.
pause
