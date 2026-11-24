"""
Helpers for the System Under Test: which build is being tested, and starting a server.

FIX_BUGS selects the build exactly as app/app.py does:
    0 (or unset/other) -> v1.0     1 -> v1.1     2 -> v1.2
"""
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_LEVEL = {"1": 1, "2": 2}.get(os.environ.get("FIX_BUGS", "0"), 0)
BUILD = ("1.0", "1.1", "1.2")[BUILD_LEVEL]


def open_until_v12(reason):
    """xfail(strict=True) on v1.0/v1.1, where the defect is known to be open; a normal
    test on v1.2, where it is fixed. strict=True turns an unexpected pass (XPASS) red."""
    return pytest.mark.xfail(BUILD_LEVEL < 2, strict=True, reason=reason)


def start_server(port, testing=True):
    """Start app/app.py on `port` with its own temporary database.

    testing=True sets TESTING=1, which the v1.2 build needs to enable the /__reset hook.
    Returns (process, base_url). The caller must terminate the process.
    """
    db = os.path.join(tempfile.gettempdir(), "tasktrack_test_%d.db" % port)
    env = dict(os.environ, PORT=str(port), TASKTRACK_DB=db)
    env.pop("TESTING", None)
    if testing:
        env["TESTING"] = "1"
    proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "app", "app.py")], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = "http://127.0.0.1:%d" % port
    for _ in range(50):
        try:
            urllib.request.urlopen(url + "/login", timeout=1)
            return proc, url
        except Exception:
            time.sleep(0.2)
    proc.kill()
    raise RuntimeError("TaskTrack server did not start on port %d" % port)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def raw_request(url, method="GET", data=None, cookies=None):
    """Send a plain HTTP request (no browser, no redirects). Returns the status code."""
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    if cookies:
        req.add_header("Cookie", "; ".join("%s=%s" % (c["name"], c["value"]) for c in cookies))
    try:
        with urllib.request.build_opener(_NoRedirect).open(req, timeout=5) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
