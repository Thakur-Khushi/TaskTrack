#!/usr/bin/env bash
# ==================================================================
#  TaskTrack - automated regression run (Selenium WebDriver + pytest)
#  Runs the full suite against build v1.0, the bug-fix build v1.1 and
#  the hardened build v1.2, and produces HTML + JUnit-XML reports in
#  the reports/ folder. Same as run_regression.bat, for Linux/macOS.
#  Usage:  ./run_regression.sh            (headless Chrome)
#          ./run_regression.sh --headed   (watch the browser)
# ==================================================================
cd "$(dirname "$0")"
if [ ! -d venv ]; then
  python3 -m venv venv
  venv/bin/python -m pip install -r requirements.txt
fi
mkdir -p reports

run() {  # $1 = FIX_BUGS level, $2 = build name, $3 = heading; rest = pytest args
  local level=$1 build=$2 heading=$3
  shift 3
  echo
  echo "===== Regression run on build $build ($heading) ====="
  FIX_BUGS=$level venv/bin/python -m pytest "$@" \
    --html="reports/report_$build.html" --self-contained-html \
    --junitxml="reports/junit_$build.xml"
}

# Like the .bat file, keep going when a build has failing tests (v1.0 is expected to).
run 0 v1.0 "before bug fixes" "$@"
run 1 v1.1 "after bug fixes" "$@"
run 2 v1.2 "exploratory + security fixes" "$@"

echo
echo "Reports written to $(pwd)/reports"
