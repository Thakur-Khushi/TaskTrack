"""Regression tests - security hardening (EXP-03, SEC-01, SEC-02).

These checks send plain HTTP requests (urllib, no browser) where the point is to act
like an attacker who does not use the app's own pages. They are xfail(strict=True)
on v1.0/v1.1, where the defects are open, and normal tests on v1.2.
"""
import pytest

from sut import open_until_v12, raw_request, start_server

pytestmark = pytest.mark.regression

SECOND_PORT = 5056  # not 5060/5061: Chrome blocks those ports


@open_until_v12("EXP-03 open: /__reset is reachable without TESTING=1")
def test_tc25_reset_hook_disabled_outside_test_mode():
    """TC-25 /__reset returns 404 when the app runs without TESTING=1 (EXP-03)"""
    proc, url = start_server(SECOND_PORT, testing=False)
    try:
        assert raw_request(url + "/__reset", "POST") == 404
    finally:
        proc.terminate()
        proc.wait(timeout=10)


@open_until_v12("SEC-01 open: no CSRF protection")
def test_tc26_post_without_csrf_token_rejected(tasks_page, base_url):
    """TC-26 A POST without a CSRF token is rejected with 400 (SEC-01)"""
    # Re-use the logged-in user's session cookie, as a forged cross-site request would.
    cookies = tasks_page.driver.get_cookies()
    status = raw_request(base_url + "/tasks/add", "POST",
                         {"title": "Forged task", "priority": "High"}, cookies)
    tasks_page.open()
    assert status == 400
    assert "Forged task" not in tasks_page.titles()


@open_until_v12("SEC-02 open: logout works with a GET request")
def test_tc27_logout_via_get_not_allowed(tasks_page, base_url):
    """TC-27 GET /logout returns 405 and does not end the session (SEC-02)"""
    assert raw_request(base_url + "/logout", "GET", cookies=tasks_page.driver.get_cookies()) == 405
    tasks_page.driver.get(base_url + "/logout")  # what <img src="/logout"> would trigger
    tasks_page.open()
    assert tasks_page.current_path() == "/tasks", "GET /logout logged the user out"
