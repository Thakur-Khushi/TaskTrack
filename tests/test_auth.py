"""Regression tests - Feature F1 Registration and F2 Login/Logout."""
import pytest

from pages.login_page import LoginPage
from pages.register_page import RegisterPage

pytestmark = pytest.mark.regression


@pytest.mark.smoke
def test_tc01_register_valid_user(driver, base_url):
    """TC-01 Register with valid details redirects to login with success message"""
    page = RegisterPage(driver, base_url).open().register("alice", "alice123", "alice123")
    assert page.current_path() == "/login"
    assert "Registration successful" in page.flash("success")


def test_tc02_register_duplicate_username(driver, base_url):
    """TC-02 Registering an existing username shows an error"""
    RegisterPage(driver, base_url).open().register("bob", "bob12345", "bob12345")
    page = RegisterPage(driver, base_url).open().register("bob", "other123", "other123")
    assert "Username already exists" in page.flash("error")


def test_tc03_register_password_mismatch(driver, base_url):
    """TC-03 Password and confirm password must match"""
    page = RegisterPage(driver, base_url).open().register("carol", "carol123", "carol999")
    assert "Passwords do not match" in page.flash("error")
    assert page.current_path() == "/register"


def test_tc04_register_short_password_rejected(driver, base_url):
    """TC-04 Password shorter than 6 characters is rejected (detects BUG-04)"""
    page = RegisterPage(driver, base_url).open().register("dave", "123", "123")
    assert page.current_path() == "/register", "weak password was accepted"
    assert "at least 6 characters" in page.flash("error")


@pytest.mark.smoke
def test_tc05_login_valid(driver, base_url):
    """TC-05 Valid credentials open the task dashboard and show the username"""
    RegisterPage(driver, base_url).open().register("erin", "erin1234", "erin1234")
    page = LoginPage(driver, base_url).open().login("erin", "erin1234")
    assert page.current_path() == "/tasks"
    assert page.find("id", "current-user").text == "erin"


def test_tc06_login_wrong_password(driver, base_url):
    """TC-06 Wrong password shows 'Invalid username or password'"""
    RegisterPage(driver, base_url).open().register("frank", "frank123", "frank123")
    page = LoginPage(driver, base_url).open().login("frank", "wrongpass")
    assert page.current_path() == "/login"
    assert "Invalid username or password" in page.flash("error")


def test_tc07_logout(tasks_page, base_url):
    """TC-07 Logout ends the session; dashboard is no longer reachable"""
    tasks_page.logout()
    assert tasks_page.current_path() == "/login"
    assert "logged out" in tasks_page.flash("success")
    tasks_page.open()
    assert tasks_page.current_path() == "/login"


def test_tc08_dashboard_requires_login(driver, base_url):
    """TC-08 Opening /tasks without logging in redirects to login"""
    page = LoginPage(driver, base_url)
    driver.get(base_url + "/tasks")
    assert page.current_path() == "/login"
    assert "Please log in first" in page.flash("error")
