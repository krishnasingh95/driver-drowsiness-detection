@echo off
title DrowsyGuard AI - Jupyter Notebook
echo ============================================================
echo   Launching Enhanced Driver Drowsiness Jupyter Notebook
echo ============================================================
cd /d "%~dp0"
call C:\Users\x1605\anaconda3\Scripts\activate.bat driverdrowsy
jupyter notebook Driver_Drowsiness_Detection_Jupyter.ipynb
pause
