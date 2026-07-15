@echo off
title Web-to-Audio Quick TTS Player
chcp 65001 > nul
cd /d "%~dp0"

set "PYTHON_EXE=.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [CANH BAO] Khong tim thay moi truong chay ao venv
    echo Vui long chay file setup.bat truoc de tu dong thiet lap thu vien.
    echo.
    pause
    exit /b 1
)

:: Khoi chay ung dung tuc thi bang python.exe cuc bo trong .venv
"%PYTHON_EXE%" clip_tts.py %*

if %errorlevel% neq 0 (
    echo.
    echo [LOI] Chuong trinh gap loi hoac bi dong dot ngot.
    pause
)
