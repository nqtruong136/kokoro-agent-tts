@echo off
title Setup Web-to-Audio Quick TTS Player
chcp 65001 > nul
cd /d "%~dp0"

echo ============================================================
echo   THIET LAP MOI TRUONG CHAY OFFLINE - WEB-TO-AUDIO QUICK TTS
echo ============================================================
echo.

:: 1. Xac dinh lenh chay UV
set "UV_CMD=.\uv.exe"
if exist ".\uv.exe" goto run_setup

where uv >nul 2>nul
if %errorlevel% equ 0 (
    set "UV_CMD=uv"
    goto run_setup
)

echo [*] Khong tim thay uv.exe cuc bo hay toan cuc.
echo [*] Dang tien hanh cai dat UV tu dong, cho giay lat...
powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
set "UV_CMD=uv"

:run_setup

:: 2. Tao virtual environment va dong bo thu vien bang UV sync
echo.
echo [*] Dang khoi tao virtual environment .venv va dong bo tat ca thu vien...
echo [*] Qua trinh nay co the mat 1-2 phut trong lan dau tien.
%UV_CMD% sync

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo   DA THIET LAP MOI TRUONG CHAY HOAN TAT!
    echo ============================================================
    echo.
    echo Bay gio ban co the click dup chuot vao file run.bat hoac
    echo clip_tts.bat de khoi chay ung dung tuc thi.
    echo.
) else (
    echo.
    echo [LOI] Thiet lap that bai. Vui long kiem tra lai ket noi mang.
)

:end
pause
