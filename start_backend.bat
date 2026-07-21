@echo off
set PYTHONIOENCODING=utf-8
cd /d "%~dp0backend"
python -m uvicorn app:app --reload --port 8000
