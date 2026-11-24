@echo off
REM Quick smoke test (critical path only) on the latest build (v1.2).
cd /d "%~dp0"
set FIX_BUGS=2
venv\Scripts\python -m pytest -m smoke %*
