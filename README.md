# TaskTrack – Mini Project (Software Testing with Selenium)

[![tests](https://github.com/Thakur-Khushi/TaskTrack/actions/workflows/tests.yml/badge.svg)](https://github.com/Thakur-Khushi/TaskTrack/actions/workflows/tests.yml)

<!-- TODO: screenshot of app -->
<!-- TODO: screenshot of HTML report -->

A small web-based task manager (Python **Flask** + **SQLite** + HTML/CSS/JS), tested with **Selenium WebDriver**, **Selenium IDE** and **pytest**.

## Problem statement → where it is covered

| Requirement | Deliverable |
|---|---|
| Small web app; choose platform and languages | [app/](app/) – Flask app; platform table in [docs/TEST_PLAN.md §2](docs/TEST_PLAN.md) |
| Concise test plan: features to be tested + bug taxonomy | [docs/TEST_PLAN.md](docs/TEST_PLAN.md) (§3 features, §5 test cases, §6 bug taxonomy) |
| Scripts for regression testing | [tests/](tests/), [run_regression.bat](run_regression.bat) / [run_regression.sh](run_regression.sh); narrated in [docs/REGRESSION_SCRIPTS.md](docs/REGRESSION_SCRIPTS.md) |
| Identify bugs using Selenium WebDriver **and** IDE | WebDriver: [tests/](tests/) · IDE: [selenium-ide/TaskTrack.side](selenium-ide/TaskTrack.side) |
| Test reports, including exploratory testing | [reports/](reports/) (HTML), [docs/TEST_SUMMARY_REPORT.md](docs/TEST_SUMMARY_REPORT.md), [docs/EXPLORATORY_TESTING.md](docs/EXPLORATORY_TESTING.md) |

## Quick start (Windows)

```bat
python -m venv venv
venv\Scripts\pip install -r requirements.txt

:: run the app  ->  http://127.0.0.1:5000
venv\Scripts\python app\app.py

:: run the whole regression (all three builds) and open the HTML reports
run_regression.bat
```
Needs Python 3.8+ and Google Chrome. The browser driver is downloaded automatically by Selenium Manager.

### Quick start (Linux / macOS)
```sh
python3 -m venv venv
venv/bin/pip install -r requirements.txt
./run_regression.sh      # full regression on v1.0, v1.1 and v1.2 -> reports/
./run_smoke.sh           # smoke tests only, on v1.2
```

## Builds
One code base, three builds, selected with the `FIX_BUGS` environment variable. This stands in for deploying successive releases, so the same regression suite can be run against each one.

| Build | `FIX_BUGS` | Contains | Search `app/app.py` for |
|---|---|---|---|
| v1.0 | `0` (default) | Initial release: 4 seeded bugs (BUG-01 … BUG-04); exploratory and security findings open | `BUG-0` |
| v1.1 | `1` | v1.0 + fixes for BUG-01 … BUG-04 | `BUG-0` |
| v1.2 | `2` | v1.1 + fixes for exploratory findings EXP-01 … EXP-04 and security findings SEC-01 … SEC-03 (CSRF tokens, POST-only logout, secret key from `SECRET_KEY`) | `EXP-0`, `SEC-0` |

```bat
set FIX_BUGS=0 & venv\Scripts\python app\app.py                 :: v1.0 – with bugs
set FIX_BUGS=1 & venv\Scripts\python app\app.py                 :: v1.1 – bugs fixed
set FIX_BUGS=2 & set TESTING=1 & venv\Scripts\python app\app.py   :: v1.2 – hardened
```
In v1.2 the `/__reset` test hook exists only when `TESTING=1`. The pytest fixture sets it automatically. Set `SECRET_KEY` for a stable session key; without it, v1.2 generates a random key at each start.

## Results at a glance
| | v1.0 | v1.1 | v1.2 |
|---|---|---|---|
| WebDriver (30 runs) | 19 pass · **4 fail** · 7 known-open | 23 pass · 0 fail · 7 known-open | 30 pass · 0 fail · 0 known-open |
| Selenium IDE (6) | 2 pass · **4 fail** | 6 pass | 6 pass |

The `reports/` folder is committed on purpose: it is the test evidence for each build.

## Useful commands
```bat
venv\Scripts\python -m pytest -m smoke              :: smoke tests only (or run_smoke.bat / ./run_smoke.sh)
venv\Scripts\python -m pytest --headed              :: watch the browser
venv\Scripts\python -m pytest --browser edge        :: Microsoft Edge
venv\Scripts\python -m pytest -k search             :: just the search tests
venv\Scripts\python tests\exploratory\explore_probe.py   :: exploratory helper (app must be running; TESTING=1 on v1.2)
npx selenium-side-runner --base-url http://127.0.0.1:5000 selenium-ide\TaskTrack.side
```

## Continuous integration
[.github/workflows/tests.yml](.github/workflows/tests.yml) runs the whole suite headless on every push and pull request, once per build (v1.0, v1.1, v1.2). The HTML and JUnit reports are uploaded as artifacts named `test-reports-v1.x`. v1.0 is expected to fail the four seeded-bug tests, so its job is green only if exactly those four fail.

## Troubleshooting
* **Edge: "Unable to obtain driver for MicrosoftEdge"** – Selenium Manager could not download msedgedriver (no internet or blocked). Download the msedgedriver that matches your Edge version from Microsoft and put it on your PATH.
* **Blank page in Chrome on ports 5060/5061** – Chrome blocks these ports as unsafe. Use 5000/5055.
* **Clicks seem to do nothing** – Chrome's "save password" popup. The test fixture already disables it; disable it the same way in your own scripts.
