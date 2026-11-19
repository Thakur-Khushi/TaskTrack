@echo off
REM ==================================================================
REM  TaskTrack - automated regression run (Selenium WebDriver + pytest)
REM  Runs the full suite against build v1.0 and the fixed build v1.1
REM  and produces HTML + JUnit-XML reports in the reports\ folder.
REM  Usage:  run_regression.bat            (headless Chrome)
REM          run_regression.bat --headed   (watch the browser)
REM ==================================================================
cd /d "%~dp0"
if not exist venv (
  python -m venv venv
  venv\Scripts\python -m pip install -r requirements.txt
)
if not exist reports mkdir reports

echo.
echo ===== Regression run on build v1.0 (before bug fixes) =====
set FIX_BUGS=0
venv\Scripts\python -m pytest %* --html=reports\report_v1.0.html --self-contained-html --junitxml=reports\junit_v1.0.xml

echo.
echo ===== Regression run on build v1.1 (after bug fixes) =====
set FIX_BUGS=1
venv\Scripts\python -m pytest %* --html=reports\report_v1.1.html --self-contained-html --junitxml=reports\junit_v1.1.xml

echo.
echo Reports written to %~dp0reports
start "" reports\report_v1.0.html
start "" reports\report_v1.1.html
