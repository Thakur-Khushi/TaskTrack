# TaskTrack – Mini Project (Software Testing with Selenium)

A small web-based task manager (Python **Flask** + **SQLite** + HTML/CSS/JS), tested with **Selenium WebDriver**, **Selenium IDE** and **pytest**.

## Problem statement → where it is covered

| Requirement | Deliverable |
|---|---|
| Small web app; choose platform and languages | [app/](app/) – Flask app; platform table in [docs/TEST_PLAN.md §2](docs/TEST_PLAN.md) |
| Concise test plan: features to be tested + bug taxonomy | [docs/TEST_PLAN.md](docs/TEST_PLAN.md) (§3 features, §5 test cases, §6 bug taxonomy) |
| Scripts for regression testing | [tests/](tests/), [run_regression.bat](run_regression.bat); narrated in [docs/REGRESSION_SCRIPTS.md](docs/REGRESSION_SCRIPTS.md) |
| Identify bugs using Selenium WebDriver **and** IDE | WebDriver: [tests/](tests/) · IDE: [selenium-ide/TaskTrack.side](selenium-ide/TaskTrack.side) |
| Test reports, including exploratory testing | [reports/](reports/) (HTML), [docs/TEST_SUMMARY_REPORT.md](docs/TEST_SUMMARY_REPORT.md), [docs/EXPLORATORY_TESTING.md](docs/EXPLORATORY_TESTING.md) |

## Quick start (Windows)

```bat
python -m venv venv
venv\Scripts\pip install -r requirements.txt

:: run the app  ->  http://127.0.0.1:5000
venv\Scripts\python app\app.py

:: run the whole regression (both builds) and open the HTML reports
run_regression.bat
```
Needs Python 3.8+ and Google Chrome. The browser driver is downloaded automatically by Selenium Manager.

### Two builds, to demonstrate regression testing
The app has 4 seeded bugs (BUG-01 … BUG-04), controlled by an environment variable:

```bat
set FIX_BUGS=0 & venv\Scripts\python app\app.py   :: v1.0 – with bugs
set FIX_BUGS=1 & venv\Scripts\python app\app.py   :: v1.1 – bugs fixed
```
Search `app/app.py` for `BUG-0` to see each bug and its fix.

## Results at a glance
| | v1.0 | v1.1 |
|---|---|---|
| WebDriver (26 runs) | 19 pass · **4 fail** · 3 known-open | 23 pass · 0 fail · 3 known-open |
| Selenium IDE (6) | 2 pass · **4 fail** | 6 pass |

## Useful commands
```bat
venv\Scripts\python -m pytest -m smoke              :: smoke tests only
venv\Scripts\python -m pytest --headed              :: watch the browser
venv\Scripts\python -m pytest --browser edge        :: Microsoft Edge
venv\Scripts\python -m pytest -k search             :: just the search tests
venv\Scripts\python tests\exploratory\explore_probe.py   :: exploratory helper (app must be running)
npx selenium-side-runner --base-url http://127.0.0.1:5000 selenium-ide\TaskTrack.side
```

## Troubleshooting
* **Edge: "Unable to obtain driver for MicrosoftEdge"** – Selenium Manager could not download msedgedriver (no internet or blocked). Download the msedgedriver that matches your Edge version from Microsoft and put it on your PATH.
* **Blank page in Chrome on ports 5060/5061** – Chrome blocks these ports as unsafe. Use 5000/5055.
* **Clicks seem to do nothing** – Chrome's "save password" popup. The test fixture already disables it; disable it the same way in your own scripts.
