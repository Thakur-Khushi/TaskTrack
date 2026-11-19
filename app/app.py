"""
TaskTrack - a small web-based task manager used as the System Under Test (SUT).

Platform : Python 3.8+, Flask (web framework), SQLite (database), HTML/CSS/JS (UI)
Run      : python app/app.py           -> http://127.0.0.1:5000

Release switch (used to demonstrate regression testing):
    FIX_BUGS=0 (default) -> "v1.0" build, contains 4 seeded bugs (BUG-01..BUG-04)
    FIX_BUGS=1           -> "v1.1" build, bugs fixed
"""
import os
import sqlite3
from functools import wraps

from flask import (Flask, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("TASKTRACK_DB", os.path.join(BASE_DIR, "tasktrack.db"))
FIX_BUGS = os.environ.get("FIX_BUGS", "0") == "1"
VERSION = "1.1" if FIX_BUGS else "1.0"

app = Flask(__name__)
app.secret_key = "tasktrack-dev-secret"


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
    return {"version": VERSION, "username": session.get("username")}


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


@app.route("/logout")
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
        if FIX_BUGS:
            sql += " AND LOWER(title) LIKE LOWER(?)"
        else:
            # BUG-02 (v1.0): search is case-sensitive ("homework" does not
            # find "Homework") because GLOB is used instead of LIKE.
            sql += " AND title GLOB ?"
        params.append(f"%{q}%" if FIX_BUGS else f"*{q}*")
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
    if not title:
        flash("Task title is required.", "error")
    elif len(title) > 100:
        flash("Task title must be 100 characters or less.", "error")
    elif priority not in ("Low", "Medium", "High"):
        flash("Invalid priority.", "error")
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
@app.route("/__reset", methods=["POST"])
def reset():
    """Wipe all data. Used only by the automated tests for a clean state."""
    db = get_db()
    db.executescript("DELETE FROM tasks; DELETE FROM users;")
    db.commit()
    return "ok"


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    print(f"TaskTrack v{VERSION} running on http://127.0.0.1:{port}")
    app.run(debug=False, port=port)
