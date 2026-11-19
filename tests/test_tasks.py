"""Regression tests - Features F3 Add, F4 Complete, F5 Delete, F6 Search, F7 Summary."""
import os

import pytest
from selenium.webdriver.common.by import By

from pages.login_page import LoginPage
from pages.register_page import RegisterPage

pytestmark = pytest.mark.regression


# ---------------------------------------------------------------- F3 Add task
@pytest.mark.smoke
def test_tc09_add_task(tasks_page):
    """TC-09 Adding a task shows it in the list with priority and due date"""
    tasks_page.add_task("Submit LP-IV journal", "High", "2026-12-01")
    assert "Task added" in tasks_page.flash("success")
    row = tasks_page.row_for("Submit LP-IV journal")
    assert row.find_element(By.CLASS_NAME, "task-priority").text == "High"
    assert row.find_element(By.CLASS_NAME, "task-due").text == "2026-12-01"


def test_tc10_empty_title_blocked(tasks_page):
    """TC-10 Empty title is blocked by browser 'required' validation"""
    tasks_page.add_task("")
    msg = tasks_page.find(By.ID, "task-title").get_attribute("validationMessage")
    assert msg, "browser should show a validation message"
    assert tasks_page.rows() == []


def test_tc11_whitespace_title_rejected(tasks_page):
    """TC-11 Title containing only spaces is rejected (detects BUG-01)"""
    tasks_page.add_task("     ")
    assert tasks_page.rows() == [], "a blank task was created"
    assert "Task title is required" in tasks_page.flash("error")


def test_tc12_title_max_length(tasks_page):
    """TC-12 Title input accepts at most 100 characters"""
    tasks_page.add_task("x" * 150)
    assert tasks_page.titles() == ["x" * 100]


# ---------------------------------------------------------------- F4 Complete
def test_tc13_mark_complete_and_undo(tasks_page):
    """TC-13 Toggling a task marks it completed and toggling again reverts it"""
    tasks_page.add_task("Read chapter 5")
    tasks_page.toggle("Read chapter 5")
    assert tasks_page.is_done("Read chapter 5")
    tasks_page.toggle("Read chapter 5")
    assert not tasks_page.is_done("Read chapter 5")


# ---------------------------------------------------------------- F5 Delete
def test_tc14_delete_task_confirm(tasks_page):
    """TC-14 Delete + confirm removes the task"""
    tasks_page.add_task("Temp task")
    tasks_page.delete("Temp task", accept=True)
    assert "Temp task" not in tasks_page.titles()
    assert "Task deleted" in tasks_page.flash("success")


def test_tc15_delete_task_cancel(tasks_page):
    """TC-15 Delete + cancel keeps the task"""
    tasks_page.add_task("Keep me")
    tasks_page.delete("Keep me", accept=False)
    assert "Keep me" in tasks_page.titles()


# ---------------------------------------------------------------- F7 Summary counters
def test_tc16_summary_counters(tasks_page):
    """TC-16 Total / Completed / Pending counters are correct (detects BUG-03)"""
    for t in ("Task A", "Task B", "Task C"):
        tasks_page.add_task(t)
    tasks_page.toggle("Task A")
    assert tasks_page.count("total") == 3
    assert tasks_page.count("completed") == 1
    assert tasks_page.count("pending") == 2


# ---------------------------------------------------------------- F6 Search
def test_tc17_search_exact_case(tasks_page):
    """TC-17 Search finds tasks matching the keyword"""
    tasks_page.add_task("Maths Homework")
    tasks_page.add_task("Buy groceries")
    tasks_page.search("Homework")
    assert tasks_page.titles() == ["Maths Homework"]


def test_tc18_search_case_insensitive(tasks_page):
    """TC-18 Search ignores letter case (detects BUG-02)"""
    tasks_page.add_task("Maths Homework")
    tasks_page.search("homework")
    assert tasks_page.titles() == ["Maths Homework"]


def test_tc19_search_no_results(tasks_page):
    """TC-19 Search with no match shows 'No tasks found'"""
    tasks_page.add_task("Maths Homework")
    tasks_page.search("zzz")
    assert tasks_page.find(By.ID, "empty-msg").text == "No tasks found."


# ---------------------------------------------------------------- Security / data isolation
def test_tc20_html_in_title_is_escaped(tasks_page):
    """TC-20 HTML/script in a title is shown as text, not executed (XSS check)"""
    payload = "<script>alert(1)</script>"
    tasks_page.add_task(payload)
    assert tasks_page.titles() == [payload]


def test_tc21_tasks_are_private_per_user(tasks_page, driver, base_url):
    """TC-21 A user cannot see another user's tasks"""
    tasks_page.add_task("student1 secret task")
    tasks_page.logout()
    RegisterPage(driver, base_url).open().register("student2", "secret456", "secret456")
    page = LoginPage(driver, base_url).open().login("student2", "secret456")
    assert page.titles() == []


# ---------------------------------------------------------------- Added after exploratory session
# These reproduce defects found during exploratory testing (docs/EXPLORATORY_TESTING.md).
# They stay marked xfail until the defects are fixed; strict=True makes the run
# flag them (XPASS -> failure) once a fix lands, so the marker gets removed.
FIXED = os.environ.get("FIX_BUGS") == "1"
# v1.0 uses SQL GLOB (so * and ? act as wildcards); v1.1 uses LIKE (so % and _ do).
_BAD = {"%", "_"} if FIXED else {"*", "?"}
_EXP01 = pytest.mark.xfail(strict=True, reason="EXP-01 open: search wildcards not escaped")


@pytest.mark.parametrize("wildcard", [
    pytest.param(w, marks=_EXP01) if w in _BAD else w for w in ["%", "_", "*", "?"]])
def test_tc22_search_wildcards_are_literal(tasks_page, wildcard):
    """TC-22 Wildcard characters in search are matched literally (EXP-01)"""
    tasks_page.add_task("Buy pens")
    tasks_page.search(wildcard)
    assert tasks_page.titles() == []


@pytest.mark.xfail(strict=True, reason="EXP-02 open: dashboard cached after logout")
def test_tc23_back_button_after_logout(tasks_page):
    """TC-23 Browser Back after logout must not show the dashboard (EXP-02)"""
    tasks_page.add_task("Private data")
    tasks_page.logout()
    tasks_page.driver.back()
    assert not tasks_page.driver.find_elements(By.ID, "add-form")
