"""
TaskTrack - a small web-based task manager used as the System Under Test (SUT).

Platform : Python 3.8+, Flask (web framework), SQLite (database), HTML/CSS/JS (UI)
Run      : python app/app.py           -> http://127.0.0.1:5000

Release switch (used to demonstrate regression testing):
    FIX_BUGS=0 (default) -> "v1.0" build, contains 4 seeded bugs (BUG-01..BUG-04)
    FIX_BUGS=1           -> "v1.1" build, bugs fixed
    FIX_BUGS=2           -> "v1.2" build, v1.1 + fixes for the exploratory findings
                            (EXP-01..EXP-04) and security hardening (SEC-01..SEC-03)
Other settings:
    TESTING=1            -> enables the /__reset test hook in v1.2 (always on in v1.0/v1.1)
    SECRET_KEY=...       -> session signing key in v1.2 (random per start if unset)
"""
import os
import secrets
import sqlite3
from datetime import date
from functools import wraps

from flask import (Flask, flash, g, redirect, render_template, request,
                   session, url_for)
from markupsafe import Markup
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("TASKTRACK_DB", os.path.join(BASE_DIR, "tasktrack.db"))
# Build level: 0 = v1.0, 1 = v1.1, 2 = v1.2. Any other value falls back to v1.0, as before.
BUILD_LEVEL = {"1": 1, "2": 2}.get(os.environ.get("FIX_BUGS", "0"), 0)
FIX_BUGS = BUILD_LEVEL >= 1   # v1.1 fixes (BUG-01..BUG-04)
FIX_V12 = BUILD_LEVEL >= 2    # v1.2 fixes (EXP-01..EXP-04, SEC-01..SEC-03)
VERSION = ("1.0", "1.1", "1.2")[BUILD_LEVEL]
TESTING = os.environ.get("TESTING") == "1"

app = Flask(__name__)
if FIX_V12:
    # SEC-03 (v1.0, v1.1): the session signing key is hard-coded in the source, so
    # anyone who has the code can forge a session cookie and log in as any user.
    app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
else:
    app.secret_key = "tasktrack-dev-secret"

csrf = None
if FIX_V12:
    # SEC-01 (v1.0, v1.1): no CSRF protection, so another website can make a
    # logged-in user's browser add or delete tasks. v1.2 checks a token on every POST.
    from flask_wtf.csrf import CSRFProtect, generate_csrf
    csrf = CSRFProtect(app)


# ---------------------------------------------------------------- database
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'Medium',
                due_date TEXT,
                done INTEGER NOT NULL DEFAULT 0
            );
            """
        )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    return {"version": VERSION, "username": session.get("username"),
            "csrf_input": csrf_input, "post_logout": FIX_V12}


def csrf_input():
    """Hidden CSRF token field for POST forms (SEC-01); renders nothing before v1.2."""
    if not FIX_V12:
        return ""
    return Markup('<input type="hidden" name="csrf_token" value="%s">' % generate_csrf())


@app.after_request
def no_cache_when_logged_in(response):
    if FIX_V12 and "user_id" in session:
        # EXP-02 (v1.0, v1.1): logged-in pages can be cached, so after logout the
        # browser Back button still shows the dashboard and the user's tasks.
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# ---------------------------------------------------------------- auth
@app.route("/")
def index():
    return redirect(url_for("tasks") if "user_id" in session else url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        error = None
        if not username or not password:
            error = "Username and password are required."
        elif FIX_BUGS and len(password) < 6:
            # BUG-04 (v1.0): minimum password length (6) shown in the UI is
            # never enforced on the server, so weak passwords are accepted.
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            db = get_db()
            if db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
                error = "Username already exists."
            else:
                db.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                           (username, generate_password_hash(password)))
                db.commit()
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("login"))
        flash(error, "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("tasks"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


# SEC-02 (v1.0, v1.1): logout is a GET link, so any page can log the user out with
# e.g. <img src="/logout">. v1.2 accepts only a POST (with CSRF token); GET -> 405.
@app.route("/logout", methods=["POST"] if FIX_V12 else ["GET"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------- tasks
@app.route("/tasks")
@login_required
def tasks():
    db = get_db()
    q = request.args.get("q", "").strip()
    sql = "SELECT * FROM tasks WHERE user_id = ?"
    params = [session["user_id"]]
    if q:
        if FIX_V12:
            # EXP-01 (v1.0, v1.1): wildcard characters typed by the user are not
            # escaped, so "%" or "_" (v1.1) and "*" or "?" (v1.0) match every task.
            esc = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            sql += " AND LOWER(title) LIKE LOWER(?) ESCAPE '\\'"
            params.append(f"%{esc}%")
        elif FIX_BUGS:
            sql += " AND LOWER(title) LIKE LOWER(?)"
            params.append(f"%{q}%")
        else:
            # BUG-02 (v1.0): search is case-sensitive ("homework" does not
            # find "Homework") because GLOB is used instead of LIKE.
            sql += " AND title GLOB ?"
            params.append(f"*{q}*")
    rows = db.execute(sql + " ORDER BY done, id DESC", params).fetchall()

    all_rows = db.execute("SELECT done FROM tasks WHERE user_id = ?",
                          (session["user_id"],)).fetchall()
    total = len(all_rows)
    completed = sum(r["done"] for r in all_rows)
    if FIX_BUGS:
        pending = total - completed
    else:
        # BUG-03 (v1.0): "Pending" counter shows the total number of tasks
        # instead of total - completed.
        pending = total
    return render_template("tasks.html", tasks=rows, q=q,
                           total=total, completed=completed, pending=pending)


@app.route("/tasks/add", methods=["POST"])
@login_required
def add_task():
    title = request.form.get("title", "")
    if FIX_BUGS:
        title = title.strip()
    # BUG-01 (v1.0): title is not stripped, so a title of only spaces
    # passes the "required" check and a blank task is created.
    priority = request.form.get("priority", "Medium")
    due_date = request.form.get("due_date") or None
    due_error = None
    if FIX_V12 and due_date:
        # EXP-04 (v1.0, v1.1): a due date in the past is accepted without a warning.
        try:
            if date.fromisoformat(due_date) < date.today():
                due_error = "Due date cannot be in the past."
        except ValueError:
            due_error = "Invalid due date."
    if not title:
        flash("Task title is required.", "error")
    elif len(title) > 100:
        flash("Task title must be 100 characters or less.", "error")
    elif priority not in ("Low", "Medium", "High"):
        flash("Invalid priority.", "error")
    elif due_error:
        flash(due_error, "error")
    else:
        db = get_db()
        db.execute("INSERT INTO tasks (user_id, title, priority, due_date) VALUES (?, ?, ?, ?)",
                   (session["user_id"], title, priority, due_date))
        db.commit()
        flash("Task added.", "success")
    return redirect(url_for("tasks"))


@app.route("/tasks/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle_task(task_id):
    db = get_db()
    db.execute("UPDATE tasks SET done = 1 - done WHERE id = ? AND user_id = ?",
               (task_id, session["user_id"]))
    db.commit()
    return redirect(url_for("tasks"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, session["user_id"]))
    db.commit()
    flash("Task deleted.", "success")
    return redirect(url_for("tasks"))


# ---------------------------------------------------------------- test hook
def reset():
    """Wipe all data. Used only by the automated tests for a clean state."""
    db = get_db()
    db.executescript("DELETE FROM tasks; DELETE FROM users;")
    db.commit()
    return "ok"


# EXP-03 (v1.0, v1.1): the /__reset hook is always registered, so anyone can wipe
# every user's data on the live server. v1.2 registers it only when TESTING=1.
if not FIX_V12 or TESTING:
    app.add_url_rule("/__reset", view_func=reset, methods=["POST"])
    if csrf is not None:
        csrf.exempt(reset)  # called by the test fixture with a plain HTTP POST


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    print(f"TaskTrack v{VERSION} running on http://127.0.0.1:{port}")
    app.run(debug=False, port=port)
