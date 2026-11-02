@echo off
title DrowsyGuard AI - Web Dashboard
echo ============================================================
echo   Starting DrowsyGuard AI Driver Safety Web Dashboard
echo ============================================================
cd /d "%~dp0"
call C:\Users\x1605\anaconda3\Scripts\activate.bat driverdrowsy
start http://localhost:5000
python app.py
pause
