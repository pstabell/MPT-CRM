@echo off
echo Starting MPT-CRM Mobile Scanner...
echo.
echo Your mobile scanner will be available at:
echo   - From this computer: http://localhost:5000
echo   - From your phone: http://YOUR-IP-ADDRESS:5000
echo.
echo To find your IP address, look for "IPv4 Address" below:
ipconfig | findstr /i "IPv4"
echo.
echo Press Ctrl+C to stop the server
echo.
python mobile_scanner.py
pause
