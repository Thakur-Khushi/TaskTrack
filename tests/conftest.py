"""
Shared pytest fixtures for the TaskTrack Selenium WebDriver suite.

Command-line options:
  --browser chrome|edge    browser to drive (default: chrome)
  --headed                 show the browser window (default: headless)
  --sut-url URL            test an already-running server instead of auto-starting one
Environment:
  FIX_BUGS=1               auto-start the fixed build v1.1 (default: v1.0 with seeded bugs)
"""
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

import pytest
from selenium import webdriver

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TESTS_DIR)
sys.path.insert(0, TESTS_DIR)
PORT = 5055
BUILD = "1.1" if os.environ.get("FIX_BUGS") == "1" else "1.0"


def pytest_addoption(parser):
    parser.addoption("--browser", default="chrome", choices=["chrome", "edge"])
    parser.addoption("--headed", action="store_true", help="show the browser window")
    parser.addoption("--sut-url", default=None, help="URL of an already running TaskTrack")


# ------------------------------------------------------------------ server
@pytest.fixture(scope="session")
def base_url(request):
    url = request.config.getoption("--sut-url")
    if url:
        yield url.rstrip("/")
        return
    db = os.path.join(tempfile.gettempdir(), "tasktrack_test.db")
    env = dict(os.environ, PORT=str(PORT), TASKTRACK_DB=db)
    proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "app", "app.py")], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = "http://127.0.0.1:%d" % PORT
    for _ in range(50):
        try:
            urllib.request.urlopen(url + "/login", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    else:
        proc.kill()
        pytest.exit("TaskTrack server did not start")
    yield url
    proc.terminate()


# ------------------------------------------------------------------ browser
@pytest.fixture(scope="session")
def browser_driver(request):
    name = request.config.getoption("--browser")
    opts = webdriver.EdgeOptions() if name == "edge" else webdriver.ChromeOptions()
    if not request.config.getoption("--headed"):
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1280,900")
    # Chrome/Edge password manager pops up "Save password?" / "Password found in a data
    # breach" dialogs after a login form is submitted; they swallow the next clicks.
    opts.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    })
    opts.add_argument("--disable-features=PasswordLeakDetection,PasswordManagerOnboarding")
    opts.add_argument("--guest")
    # Selenium Manager (built into Selenium 4.6+) downloads the matching driver automatically.
    drv = webdriver.Edge(options=opts) if name == "edge" else webdriver.Chrome(options=opts)
    drv.implicitly_wait(1)
    yield drv
    drv.quit()


@pytest.fixture
def driver(browser_driver, base_url):
    """Clean state for every test: wipe the database and the browser cookies."""
    urllib.request.urlopen(urllib.request.Request(base_url + "/__reset", method="POST"))
    browser_driver.get(base_url + "/login")
    browser_driver.delete_all_cookies()
    return browser_driver


@pytest.fixture
def tasks_page(driver, base_url):
    """A registered and logged-in user; returns the TasksPage object."""
    from pages.login_page import LoginPage
    from pages.register_page import RegisterPage
    RegisterPage(driver, base_url).open().register("student1", "secret123", "secret123")
    return LoginPage(driver, base_url).open().login("student1", "secret123")


# ------------------------------------------------------------------ report hooks
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach a screenshot + URL to the HTML report when a UI test fails."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        drv = item.funcargs.get("browser_driver")
        html = item.config.pluginmanager.getplugin("html")
        if drv is not None and html is not None:
            extras = getattr(report, "extras", [])
            extras.append(html.extras.url(drv.current_url))
            extras.append(html.extras.png(drv.get_screenshot_as_base64(), "Screenshot"))
            report.extras = extras
    doc = (item.function.__doc__ or "").strip().splitlines()
    report.description = doc[0] if doc else ""


def pytest_html_report_title(report):
    report.title = "TaskTrack Regression Report - build v%s" % BUILD


def pytest_html_results_table_header(cells):
    cells.insert(2, "<th>Description</th>")


def pytest_html_results_table_row(report, cells):
    cells.insert(2, "<td>%s</td>" % getattr(report, "description", ""))


def pytest_configure(config):
    if config.pluginmanager.hasplugin("metadata"):
        from pytest_metadata.plugin import metadata_key
        md = config.stash[metadata_key]
        md["System Under Test"] = "TaskTrack (Python Flask + SQLite)"
        md["Build"] = "v" + BUILD
        md["Browser"] = config.getoption("--browser")
        md["Tool"] = "Selenium WebDriver 4 + pytest"
