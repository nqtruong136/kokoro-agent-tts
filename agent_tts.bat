@echo off
title Web-to-Audio Agent Playback
chcp 65001 > nul
cd /d "%~dp0"

set "PYTHON_EXE=.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    where uv >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=uv run python"
    ) else (
        set "PYTHON_EXE=python"
    )
)

:: Khoi chay o che do non-interactive va dong cua so ngay sau khi phat xong
"%PYTHON_EXE%" clip_tts.py --non-interactive %*
exit /b %errorlevel%
