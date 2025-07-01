@echo off
echo WS7 Wavelength Meter Server - Setup Script
echo ==========================================

echo.
echo Installing required Python packages...
pip install -r requirements.txt

echo.
echo Checking Python version...
python --version

echo.
echo Testing WS7 module in debug mode...
python wlm.py --debug 1 2 3

echo.
echo Setup completed!
echo.
echo Usage:
echo   Basic measurement:       python wlm.py
echo   Debug mode:              python wlm.py --debug
echo   Start server:            python WS7_server_threading.py
echo   Start server (debug):    python WS7_server_threading.py --debug
echo.
pause
