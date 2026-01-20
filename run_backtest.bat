@echo off
title Nifty Options Strategy Backtest

REM Angel One Credentials
set ANGEL_API_KEY=YOUR_API_KEY_HERE
set ANGEL_CLIENT_ID=YOUR_CLIENT_ID_HERE
set ANGEL_PASSWORD=YOUR_4_DIGIT_MPIN_HERE
set ANGEL_TOTP_SECRET=YOUR_TOTP_SECRET_HERE

echo ========================================
echo   NIFTY OPTIONS STRATEGY BACKTEST
echo ========================================
echo.
echo This will backtest your strategy using
echo historical data from Angel One SmartAPI
echo.
echo Press any key to start...
pause > nul

python backtest.py

echo.
echo ========================================
echo   BACKTEST COMPLETED
echo ========================================
echo.
pause
