"""
Exploratory testing helper (session-based).

This is NOT a pass/fail regression test. It drives the browser through the
"charters" of the exploratory session and PRINTS what it observed, so the
tester can judge each behaviour and log bugs in docs/EXPLORATORY_TESTING.md.

Usage:  start the app (python app/app.py), then
        python tests/exploratory/explore_probe.py [http://127.0.0.1:5000]
"""
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from selenium import webdriver  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402

from pages.login_page import LoginPage  # noqa: E402
from pages.register_page import RegisterPage  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000").rstrip("/")
SHOTS = os.path.join(os.path.dirname(__file__), "..", "..", "reports", "exploratory")
os.makedirs(SHOTS, exist_ok=True)


def note(charter, observation):
    print("[%s] %s" % (charter, observation))


def shot(d, name):
    d.save_screenshot(os.path.join(SHOTS, name + ".png"))


opts = webdriver.ChromeOptions()
opts.add_argument("--headless=new")
opts.add_argument("--window-size=1280,900")
opts.add_argument("--guest")
opts.add_experimental_option("prefs", {"credentials_enable_service": False,
                                       "profile.password_manager_enabled": False,
                                       "profile.password_manager_leak_detection": False})
d = webdriver.Chrome(options=opts)
d.implicitly_wait(1)
try:
    urllib.request.urlopen(urllib.request.Request(BASE + "/__reset", method="POST"))
    user = "explorer%d" % int(time.time())
    RegisterPage(d, BASE).open().register(user, "secret123", "secret123")
    tp = LoginPage(d, BASE).open().login(user, "secret123")
    note("SETUP", "logged in as %s, build %s" % (user, d.find_element(By.ID, "app-version").text))

    # CH-1 Search with special / wildcard characters
    tp.add_task("Plan 100% attendance")
    tp.add_task("Buy pens")
    tp.add_task("file_name fix")
    for q in ["%", "_", "*", "?", "[", "100%"]:
        tp.search(q)
        note("CH-1 search", "query %-6r -> %s" % (q, tp.titles()))
    shot(d, "ch1_search_percent")
    d.get(BASE + "/tasks")

    # CH-2 Due date in the past / invalid
    tp.add_task("Past due task", due="2001-01-01")
    note("CH-2 due date", "past date accepted, row due = %s"
         % tp.row_for("Past due task").find_element(By.CLASS_NAME, "task-due").text)

    # CH-3 Duplicate titles and double-submit
    tp.add_task("Duplicate")
    tp.add_task("Duplicate")
    note("CH-3 duplicates", "rows titled 'Duplicate': %d" % tp.titles().count("Duplicate"))

    # CH-4 Unicode / long text
    tp.add_task("होमवर्क पूरा करो ✅")
    note("CH-4 unicode", "unicode title shown as: %r" % tp.titles()[0])
    tp.search("होमवर्क")
    note("CH-4 unicode", "search unicode -> %s" % tp.titles())
    d.get(BASE + "/tasks")

    # CH-5 Browser BACK after logout
    tp.logout()
    d.back()
    time.sleep(0.5)
    note("CH-5 back after logout", "url=%s, dashboard visible=%s" % (
        d.current_url, bool(d.find_elements(By.ID, "add-form"))))
    shot(d, "ch5_back_after_logout")
    d.refresh()
    note("CH-5 back after logout", "after refresh url=%s" % d.current_url)

    # CH-6 Direct URL manipulation (GET on POST-only action)
    LoginPage(d, BASE).open().login(user, "secret123")
    d.get(BASE + "/tasks/1/delete")
    note("CH-6 url tampering", "GET /tasks/1/delete -> title=%r" % d.title)
    d.get(BASE + "/__reset")
    note("CH-6 url tampering", "GET /__reset -> title=%r (endpoint exists publicly)" % d.title)

    # CH-7 Username edge cases
    d.get(BASE + "/logout")
    RegisterPage(d, BASE).open().register("  spaced  ", "secret123", "secret123")
    LoginPage(d, BASE).open().login("spaced", "secret123")
    note("CH-7 username", "'  spaced  ' registered, login as 'spaced' -> %s" % d.current_url)
    d.get(BASE + "/logout")
    RegisterPage(d, BASE).open().register("Explorer", "secret123", "secret123")
    note("CH-7 username", "register 'Explorer' when 'explorer…' exists -> %r"
         % (RegisterPage(d, BASE).flash("success") or RegisterPage(d, BASE).flash("error")))
finally:
    d.quit()
