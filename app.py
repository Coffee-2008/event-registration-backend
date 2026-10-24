"""
Celestius Backend Task - Event Registration API
Event: Backend Development Workshop (20 October 2026), capacity 50.

Stack: Python + Flask + SQLite (no extra database setup needed).
Run:   python app.py
"""

import os
import re
import sqlite3
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "registrations.db")
CAPACITY = 50
EVENT = {
    "name": "Backend Development Workshop",
    "date": "20 October 2026",
    "capacity": CAPACITY,
}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- database helpers ----------

def get_db():
    # isolation_level=None lets us control transactions by hand (needed below)
    conn = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS registrations (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
            college       TEXT,
            registered_at TEXT NOT NULL
        )
        """
    )
    conn.close()


def row_to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "college": row["college"],
        "registered_at": row["registered_at"],
    }


def error(message, status):
    return jsonify({"error": message}), status


# ---------- routes ----------

@app.get("/")
def home():
    conn = get_db()
    filled = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
    conn.close()
    return jsonify(
        {
            "event": EVENT,
            "seats_filled": filled,
            "seats_left": CAPACITY - filled,
            "endpoints": [
                "POST /register",
                "GET /registrations",
                "GET /registrations/<id>",
            ],
        }
    )


@app.post("/register")
def register():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Send the details as JSON.", 400)

    name = str(data.get("name") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    college = str(data.get("college") or "").strip() or None

    # 1. check the details
    problems = []
    if not name:
        problems.append("name is required")
    if not email:
        problems.append("email is required")
    elif not EMAIL_PATTERN.match(email):
        problems.append("email is not valid")
    if problems:
        return jsonify({"error": "Invalid or missing information", "details": problems}), 400

    conn = get_db()
    try:
        # BEGIN IMMEDIATE locks the database for writing, so two people
        # registering at the same moment can't both grab the last seat.
        conn.execute("BEGIN IMMEDIATE")

        # 2. already registered?
        if conn.execute(
            "SELECT 1 FROM registrations WHERE email = ?", (email,)
        ).fetchone():
            conn.execute("ROLLBACK")
            return error("This email is already registered.", 409)

        # 3. any seats left?
        filled = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
        if filled >= CAPACITY:
            conn.execute("ROLLBACK")
            return error("Event is full", 409)

        # 4. save it
        registered_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cur = conn.execute(
            "INSERT INTO registrations (name, email, college, registered_at) VALUES (?, ?, ?, ?)",
            (name, email, college, registered_at),
        )
        conn.execute("COMMIT")

        return (
            jsonify(
                {
                    "message": "Registration successful",
                    "registration": {
                        "id": cur.lastrowid,
                        "name": name,
                        "email": email,
                        "college": college,
                        "registered_at": registered_at,
                    },
                    "seats_filled": filled + 1,
                    "seats_left": CAPACITY - (filled + 1),
                }
            ),
            201,
        )
    except Exception:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        return error("Something went wrong on the server.", 500)
    finally:
        conn.close()


@app.get("/registrations")
def list_registrations():
    conn = get_db()
    rows = conn.execute("SELECT * FROM registrations ORDER BY id").fetchall()
    conn.close()
    return jsonify(
        {
            "event": EVENT["name"],
            "seats_filled": len(rows),
            "capacity": CAPACITY,
            "registrations": [row_to_dict(r) for r in rows],
        }
    )


@app.get("/registrations/<int:reg_id>")
def get_registration(reg_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM registrations WHERE id = ?", (reg_id,)).fetchone()
    conn.close()
    if row is None:
        return error("Registration not found.", 404)
    return jsonify(row_to_dict(row))


@app.get("/registrations/email/<path:email>")
def get_registration_by_email(email):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM registrations WHERE email = ?", (email.strip().lower(),)
    ).fetchone()
    conn.close()
    if row is None:
        return error("Registration not found.", 404)
    return jsonify(row_to_dict(row))


@app.errorhandler(404)
def not_found(_):
    return error("Route not found.", 404)


@app.errorhandler(405)
def wrong_method(_):
    return error("Method not allowed for this route.", 405)


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
