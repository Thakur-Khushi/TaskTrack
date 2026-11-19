# Regression Test Scripts – Narration

Regression testing re-runs the same tests on every new build. The aim is to prove that (a) the reported bugs are fixed and (b) nothing that used to work has broken. For TaskTrack, the same suite runs on **v1.0** (with the reported bugs) and on **v1.1** (the bug-fix release).

## 1. How the suite is organised

```
tests/
├── conftest.py          # fixtures: starts the server, opens the browser, resets data, report hooks
├── pages/               # Page Object Model – one class per screen
│   ├── base_page.py     # common helpers: open, type, click, submit_and_wait, flash
│   ├── login_page.py
│   ├── register_page.py
│   └── tasks_page.py    # add_task, toggle, delete, search, count …
├── test_auth.py         # TC-01 … TC-08  (registration, login, logout)
├── test_tasks.py        # TC-09 … TC-23  (tasks, search, counters, security)
└── exploratory/explore_probe.py   # helper for the exploratory session (not pass/fail)
selenium-ide/TaskTrack.side        # 6 record & playback tests (IDE-01 … IDE-06)
run_regression.bat                 # one-click regression run on both builds
run_smoke.bat                      # quick smoke run
```

### Why the Page Object Model?
Locators such as `id=task-title` live in a single place. If the UI changes, you update one page class and every test keeps working. The tests then read like plain English:

```python
def test_tc16_summary_counters(tasks_page):
    for t in ("Task A", "Task B", "Task C"):
        tasks_page.add_task(t)
    tasks_page.toggle("Task A")
    assert tasks_page.count("total") == 3
    assert tasks_page.count("completed") == 1
    assert tasks_page.count("pending") == 2      # fails on v1.0 -> BUG-03
```

## 2. What happens in one test (step by step)

1. **`base_url` fixture** (once per run) starts `app/app.py` on port 5055 with a separate test database and waits until `/login` responds.
2. **`browser_driver` fixture** (once per run) opens headless Chrome through Selenium WebDriver. Selenium Manager downloads a matching ChromeDriver automatically. The password manager is turned off, because its "save password" popup swallows clicks.
3. **`driver` fixture** (before every test) calls `POST /__reset` to empty the database and deletes cookies. Every test therefore starts from the same clean state and does not depend on other tests.
4. **`tasks_page` fixture** registers `student1` and logs in, for tests that need a logged-in user.
5. The test drives the UI through page objects. `submit_and_wait()` clicks a button and **waits for the next page to load** (it checks for staleness of the old `<html>` element). This prevents flaky failures where the test checks too early.
6. `assert` statements compare actual against expected results.
7. **On failure**, a hook takes a screenshot and stores the current URL in the HTML report.

## 3. Running the scripts

| Command | What it does |
|---|---|
| `run_regression.bat` | Full suite on v1.0, then on v1.1 → `reports/report_v1.0.html`, `report_v1.1.html`, JUnit XML |
| `run_regression.bat --headed` | Same, but you can watch the browser |
| `run_smoke.bat` | Only the `@pytest.mark.smoke` tests (TC-01, TC-05, TC-09) |
| `venv\Scripts\python -m pytest -k search` | Only the search tests |
| `venv\Scripts\python -m pytest --browser edge` | Run on Microsoft Edge |
| `set FIX_BUGS=1` then `pytest` | Choose the build manually |

The `FIX_BUGS` environment variable selects the build: `0` = v1.0, `1` = v1.1. This stands in for deploying a new release of the application.

## 4. Markers used
* `@pytest.mark.smoke` – critical path, run on every build.
* `@pytest.mark.regression` – applied to every test in both files.
* `@pytest.mark.xfail(strict=True, reason="EXP-0x open …")` – reproduces a known **open** defect found during exploratory testing. It is reported as *xfailed*, so it does not hide new failures. Because of `strict=True`, the moment a developer fixes the defect the test turns red as "XPASS". That reminds the team to remove the marker and keep the test as a normal regression check.

## 5. Selenium IDE scripts
`selenium-ide/TaskTrack.side` holds six recorded tests that check the same bugs without writing code:

| IDE test | Checks | v1.0 | v1.1 |
|---|---|---|---|
| IDE-01 Register and login | F1, F2 | Pass | Pass |
| IDE-02 Invalid login shows error | F2 | Pass | Pass |
| IDE-03 Add, complete and delete task | F3, F4, F5, F7 | **Fail (BUG-03)** | Pass |
| IDE-04 Search is case-insensitive | F6 | **Fail (BUG-02)** | Pass |
| IDE-05 Blank (spaces) title rejected | F3 | **Fail (BUG-01)** | Pass |
| IDE-06 Weak password rejected | F1 | **Fail (BUG-04)** | Pass |

**Open in Selenium IDE:** install the *Selenium IDE* extension in Chrome or Edge → *Open an existing project* → choose `TaskTrack.side`. Start the app (`python app/app.py`). Then click **Run all tests** to watch each command run, and use **Record** to add new steps.

**Run from the command line:**
`npx selenium-side-runner --base-url http://127.0.0.1:5000 selenium-ide/TaskTrack.side`

Notes from making the IDE tests reliable:
* Each test creates its own unique user with `executeScript  return 'ide' + Date.now()`, so tests can run in any order.
* After a click that reloads the page, the checks use `waitForText` / `waitForElementPresent` rather than `assertText`. These still fail if the expected value never appears. In the first version, the assert fired before the page reloaded and gave a false failure.
* The delete confirmation is auto-accepted with `window.confirm = () => true`, because newer IDE versions dropped `chooseOkOnNextConfirmation`.
* `type` cannot enter an all-spaces value, so IDE-05 sets it with `executeScript`.
