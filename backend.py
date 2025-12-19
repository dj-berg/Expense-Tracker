# ======================================================
# APPLICATION IMPORTS & SETUP
# Purpose: Configure Flask app and core dependencies
# ======================================================

from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta


# ======================================================
# FLASK APPLICATION CONFIGURATION
# Purpose: Initialize Flask with custom folder structure
# ======================================================

app = Flask(
    __name__,
    template_folder="frontend/Structure",   # HTML files
    static_folder="frontend/Styling"        # CSS & JS files
)

app.secret_key = "dev_secret_key"  # Used for session management (change in prod)

DB_NAME = "database.db"


# ======================================================
# DATABASE CONNECTION HELPERS
# Purpose: Create and manage SQLite connections
# ======================================================

def get_db():
    """Open a SQLite connection with row-based access."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initialize database schema.
    Creates required tables if they do not exist.
    """
    conn = get_db()
    cur = conn.cursor()

    # ---------------- USERS TABLE ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # ---------------- EXPENSES TABLE ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ======================================================
# AUTHENTICATION HELPERS
# Purpose: Manage session-based user access
# ======================================================

def current_user():
    """Return the currently logged-in user ID (if any)."""
    return session.get("user_id")


def login_required():
    """
    Guard helper for protected routes.
    Redirects unauthenticated users to login.
    """
    if not current_user():
        return redirect(url_for("login"))


# ======================================================
# ROUTES: LANDING & AUTHENTICATION
# ======================================================

@app.route("/")
def index():
    """Landing / start page."""
    return render_template("start_page.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """
    User registration.
    - Hashes password
    - Stores user in SQL database
    """
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # Email already exists
            return render_template("signup.html", error="Email already exists.")
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    User login.
    - Verifies credentials
    - Sets session on success
    """
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid credentials.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Clear session and return to login page."""
    session.clear()
    return redirect(url_for("login"))


# ======================================================
# ROUTES: DASHBOARD & ANALYTICS
# ======================================================

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """
    Dashboard page.
    Handles:
    - Expense insertion
    - Weekly filtering
    - SQL aggregation for analytics
    """
    if not current_user():
        return redirect(url_for("login"))

    user_id = current_user()
    conn = get_db()
    cur = conn.cursor()

    # ---------------- ADD EXPENSE ----------------
    if request.method == "POST":
        amount = float(request.form["amount"])
        category = request.form["category"]
        date = request.form["date"]

        cur.execute("""
            INSERT INTO expenses (user_id, amount, category, date)
            VALUES (?, ?, ?, ?)
        """, (user_id, amount, category, date))

        conn.commit()

    # ---------------- WEEK SELECTION ----------------
    selected_week = request.args.get("week")

    if selected_week:
        year, week = map(int, selected_week.split("-W"))
        start_date = datetime.fromisocalendar(year, week, 1)
    else:
        today = datetime.today()
        start_date = today - timedelta(days=today.weekday())
        selected_week = today.strftime("%Y-W%V")

    end_date = start_date + timedelta(days=6)

    # ---------------- SQL AGGREGATION ----------------
    cur.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE user_id = ?
        AND date BETWEEN ? AND ?
        GROUP BY category
    """, (user_id, start_date.date(), end_date.date()))

    rows = cur.fetchall()
    conn.close()

    # ---------------- DATA PREPARATION ----------------
    categories = [row["category"] for row in rows]
    amounts = [row["total"] for row in rows]

    total_spent = round(sum(amounts), 2)
    top_category = categories[amounts.index(max(amounts))] if amounts else None

    return render_template(
        "dashboard.html",
        selected_week=selected_week,
        total_spent=total_spent,
        top_category=top_category,
        categories=categories,
        amounts=amounts
    )


# ======================================================
# APPLICATION ENTRY POINT
# Purpose: Initialize DB and start Flask server
# ======================================================

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
