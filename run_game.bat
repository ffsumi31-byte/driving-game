@echo off
cd /d "%~dp0"
start "NEON DRIFT" http://localhost:8000
py server.py
pause
