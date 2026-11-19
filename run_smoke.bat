@echo off
REM Quick smoke test (critical path only) on the fixed build.
cd /d "%~dp0"
set FIX_BUGS=1
venv\Scripts\python -m pytest -m smoke %*
