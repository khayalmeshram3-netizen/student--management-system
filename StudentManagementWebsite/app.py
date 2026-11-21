import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

from flask import (
    Flask, abort, flash, g, redirect, render_template,
    request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "students.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY", "development-key-change-before-deployment"
)

# Demo login. Change these before using the project outside your own computer.
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = generate_password_hash(
    os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")
)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                age INTEGER NOT NULL CHECK(age > 0),
                course TEXT NOT NULL,
                marks REAL NOT NULL CHECK(marks >= 0 AND marks <= 100)
            )
        """)
        db.commit()


def grade_for(marks):
    marks = float(marks)
    if marks >= 90:
        return "A+"
    if marks >= 80:
        return "A"
    if marks >= 70:
        return "B"
    if marks >= 60:
        return "C"
    if marks >= 40:
        return "D"
    return "F"


@app.template_filter("grade")
def grade_filter(marks):
    return grade_for(marks)


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view


def make_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


@app.context_processor
def inject_template_values():
    return {"csrf_token": make_csrf_token}


@app.before_request
def check_csrf():
    if request.method == "POST":
        sent_token = request.form.get("_csrf_token", "")
        saved_token = session.get("_csrf_token", "")
        if not saved_token or not secrets.compare_digest(sent_token, saved_token):
            abort(400, description="Security token missing or invalid. Refresh the page and try again.")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session.clear()
            session["logged_in"] = True
            session["username"] = username
            flash("Login successful. Welcome!", "success")
            return redirect(url_for("dashboard"))
        flash("Incorrect username or password.", "error")

    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    course_count = db.execute("SELECT COUNT(DISTINCT course) FROM students").fetchone()[0]
    average = db.execute("SELECT AVG(marks) FROM students").fetchone()[0] or 0
    recent = db.execute("SELECT * FROM students ORDER BY id DESC LIMIT 5").fetchall()
    return render_template(
        "dashboard.html",
        total=total,
        course_count=course_count,
        average=round(average, 1),
        recent=recent
    )


@app.route("/students")
@login_required
def students():
    search = request.args.get("q", "").strip()
    db = get_db()

    if search:
        pattern = f"%{search}%"
        records = db.execute("""
            SELECT * FROM students
            WHERE name LIKE ? OR email LIKE ? OR course LIKE ? OR CAST(id AS TEXT) LIKE ?
            ORDER BY id DESC
        """, (pattern, pattern, pattern, pattern)).fetchall()
    else:
        records = db.execute("SELECT * FROM students ORDER BY id DESC").fetchall()

    return render_template("students.html", students=records, search=search)


def read_student_form():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    course = request.form.get("course", "").strip()

    try:
        age = int(request.form.get("age", "0"))
        marks = float(request.form.get("marks", "-1"))
    except ValueError:
        raise ValueError("Age and marks must be valid numbers.")

    if not name or not email or not course:
        raise ValueError("Please fill in every field.")
    if age < 1 or age > 120:
        raise ValueError("Enter an age between 1 and 120.")
    if marks < 0 or marks > 100:
        raise ValueError("Marks must be between 0 and 100.")

    return name, email, age, course, marks


@app.route("/students/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        try:
            values = read_student_form()
            get_db().execute(
                "INSERT INTO students (name, email, age, course, marks) VALUES (?, ?, ?, ?, ?)",
                values
            )
            get_db().commit()
            flash("Student added successfully.", "success")
            return redirect(url_for("students"))
        except ValueError as error:
            flash(str(error), "error")
        except sqlite3.IntegrityError:
            flash("That email address is already registered.", "error")

    return render_template("student_form.html", page_title="Add Student", student=None)


@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    db = get_db()
    student = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if student is None:
        abort(404)

    if request.method == "POST":
        try:
            values = read_student_form()
            db.execute("""
                UPDATE students
                SET name = ?, email = ?, age = ?, course = ?, marks = ?
                WHERE id = ?
            """, (*values, student_id))
            db.commit()
            flash("Student details updated.", "success")
            return redirect(url_for("students"))
        except ValueError as error:
            flash(str(error), "error")
        except sqlite3.IntegrityError:
            flash("That email address is already used by another student.", "error")

    return render_template("student_form.html", page_title="Edit Student", student=student)


@app.post("/students/<int:student_id>/delete")
@login_required
def delete_student(student_id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    flash("Student record deleted.", "success")
    return redirect(url_for("students"))


@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, message=error.description), 400


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="The page or student record was not found."), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
