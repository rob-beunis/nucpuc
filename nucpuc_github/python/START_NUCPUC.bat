@echo off
cd /d "%~dp0"
python nucpuc.py %*
if errorlevel 1 pause
