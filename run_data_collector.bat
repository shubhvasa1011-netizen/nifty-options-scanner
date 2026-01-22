@echo off
title Options Data Collector

REM Angel One Credentials
set ANGEL_API_KEY=YOUR_API_KEY_HERE
set ANGEL_CLIENT_ID=YOUR_CLIENT_ID_HERE
set ANGEL_PASSWORD=YOUR_4_DIGIT_MPIN_HERE
set ANGEL_TOTP_SECRET=YOUR_TOTP_SECRET_HERE

echo ========================================
echo   OPTIONS DATA COLLECTOR
echo ========================================
echo.
echo This will collect live options data
echo every minute during market hours.
echo.
echo Data will be saved to:
echo options_historical_data.json
echo.
echo Press any key to start...
pause > nul

python data_collector.py

pause
