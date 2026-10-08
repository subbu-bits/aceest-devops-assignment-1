"""
ACEest Fitness & Gym - Flask web application.

This is the web (Flask) version of the ACEest Tkinter desktop app
(versions 1.0 -> 3.2.4). The business logic is the same:
fitness programs, calorie estimates, BMI, clients, progress,
workouts and a simple program generator. Instead of buttons and
windows, everything is exposed as JSON API endpoints.
"""
import os
import random
import sqlite3

from flask import Flask, current_app, g, jsonify, request

# ---------------------------------------------------------------------------
# Static data (taken from Aceestver-1.1.py and Aceestver-3.2.4.py)
# ---------------------------------------------------------------------------
PROGRAMS = {
    "FL": {
        "name": "Fat Loss",
        "workout": [
            "Mon: Back Squat 5x5 + Core",
            "Tue: EMOM 20min Assault Bike",
            "Wed: Bench Press + 21-15-9",
            "Thu: Deadlift + Box Jumps",
            "Fri: Zone 2 Cardio 30min",
        ],
        "diet": [
            "Breakfast: Egg Whites + Oats",
            "Lunch: Grilled Chicken + Brown Rice",
            "Dinner: Fish Curry + Millet Roti",
            "Target: ~2000 kcal",
        ],
        "calorie_factor": 22,
    },
    "MG": {
        "name": "Muscle Gain",
        "workout": [
            "Mon: Squat 5x5",
            "Tue: Bench 5x5",
            "Wed: Deadlift 4x6",
            "Thu: Front Squat 4x8",
            "Fri: Incline Press 4x10",
            "Sat: Barbell Rows 4x10",
        ],
        "diet": [
            "Breakfast: Eggs + Peanut Butter Oats",
            "Lunch: Chicken Biryani",
            "Dinner: Mutton Curry + Rice",
            "Target: ~3200 kcal",
        ],
        "calorie_factor": 35,
    },
    "BG": {
        "name": "Beginner",
        "workout": [
            "Full Body Circuit: Air Squats, Ring Rows, Push-ups",
            "Focus: Technique & Consistency",
        ],
        "diet": [
            "Balanced Tamil Meals",
            "Idli / Dosa / Rice + Dal",
            "Protein Target: 120g/day",
        ],
        "calorie_factor": 26,
    },
}

PROGRAM_TEMPLATES = {
    "FL": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],
    "MG": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],
    "BG": ["Full Body 3x/week", "Light Strength + Mobility"],
}

WORKOUT_TYPES = ["Strength", "Hypertrophy", "Cardio", "Mobility"]


# ---------------------------------------------------------------------------
# Pure business logic (easy to unit test, no Flask or DB needed)
# ---------------------------------------------------------------------------
def calculate_calories(weight_kg, program_code):
    """Daily calorie estimate = body weight x program factor."""
    if program_code not in PROGRAMS:
        raise ValueError(f"Unknown program: {program_code}")
    if weight_kg is None or weight_kg <= 0:
        raise ValueError("Weight must be a positive number")
    return int(weight_kg * PROGRAMS[program_code]["calorie_factor"])


def calculate_bmi(weight_kg, height_cm):
    """BMI = weight (kg) / height (m) squared, rounded to 1 decimal."""
    if weight_kg is None or weight_kg <= 0:
        raise ValueError("Weight must be a positive number")
    if height_cm is None or height_cm <= 0:
        raise ValueError("Height must be a positive number")
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def bmi_category(bmi):
    """WHO BMI categories."""
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def validate_adherence(value):
    """Adherence must be a whole number between 0 and 100."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("Adherence must be an integer")
    if value < 0 or value > 100:
        raise ValueError("Adherence must be between 0 and 100")
    return value


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    age INTEGER,
    height REAL,
    weight REAL,
    program TEXT,
    calories INTEGER,
    membership_status TEXT DEFAULT 'Active'
);
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    week TEXT NOT NULL,
    adherence INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    date TEXT NOT NULL,
    workout_type TEXT NOT NULL,
    duration_min INTEGER,
    notes TEXT
);
"""


def get_db():
    """Open one DB connection per request and reuse it."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def find_client(name):
    return get_db().execute(
        "SELECT * FROM clients WHERE name = ?", (name,)
    ).fetchone()


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
def create_app(db_path=None):
    """Create the Flask app. Tests pass their own temporary db_path."""
    app = Flask(__name__)
    app.config["DATABASE"] = db_path or os.environ.get(
        "ACEEST_DB", "aceest_fitness.db"
    )
    init_db(app.config["DATABASE"])
    app.teardown_appcontext(close_db)

    def error(message, status=400):
        return jsonify({"error": message}), status

    # ---------------- General ----------------
    @app.get("/")
    def home():
        return jsonify({
            "app": "ACEest Fitness & Gym",
            "status": "running",
            "endpoints": ["/health", "/programs", "/calories", "/bmi",
                          "/clients"],
        })

    @app.get("/health")
    def health():
        return jsonify({"status": "healthy"})

    # ---------------- Programs ----------------
    @app.get("/programs")
    def list_programs():
        return jsonify({code: p["name"] for code, p in PROGRAMS.items()})

    @app.get("/programs/<code>")
    def get_program(code):
        program = PROGRAMS.get(code.upper())
        if program is None:
            return error("Program not found", 404)
        return jsonify({"code": code.upper(), **program})

    # ---------------- Calculators ----------------
    @app.post("/calories")
    def calories():
        data = request.get_json(silent=True) or {}
        try:
            weight = float(data.get("weight", 0))
            result = calculate_calories(weight, data.get("program"))
        except (TypeError, ValueError) as exc:
            return error(str(exc))
        return jsonify({"program": data["program"], "calories": result})

    @app.post("/bmi")
    def bmi():
        data = request.get_json(silent=True) or {}
        try:
            value = calculate_bmi(float(data.get("weight", 0)),
                                  float(data.get("height", 0)))
        except (TypeError, ValueError) as exc:
            return error(str(exc))
        return jsonify({"bmi": value, "category": bmi_category(value)})

    # ---------------- Clients ----------------
    @app.get("/clients")
    def list_clients():
        rows = get_db().execute(
            "SELECT * FROM clients ORDER BY name").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/clients")
    def create_client():
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        program = data.get("program")
        if not name:
            return error("Client name is required")
        if program not in PROGRAMS:
            return error("A valid program (FL, MG, BG) is required")
        try:
            weight = float(data.get("weight", 0))
            calories_value = calculate_calories(weight, program)
        except (TypeError, ValueError) as exc:
            return error(str(exc))
        if find_client(name):
            return error("Client already exists", 409)

        db = get_db()
        db.execute(
            "INSERT INTO clients (name, age, height, weight, program,"
            " calories) VALUES (?, ?, ?, ?, ?, ?)",
            (name, data.get("age"), data.get("height"), weight, program,
             calories_value),
        )
        db.commit()
        return jsonify(dict(find_client(name))), 201

    @app.get("/clients/<name>")
    def get_client(name):
        row = find_client(name)
        if row is None:
            return error("Client not found", 404)
        return jsonify(dict(row))

    @app.delete("/clients/<name>")
    def delete_client(name):
        if find_client(name) is None:
            return error("Client not found", 404)
        db = get_db()
        db.execute("DELETE FROM progress WHERE client_name = ?", (name,))
        db.execute("DELETE FROM workouts WHERE client_name = ?", (name,))
        db.execute("DELETE FROM clients WHERE name = ?", (name,))
        db.commit()
        return jsonify({"deleted": name})

    # ---------------- Progress ----------------
    @app.post("/clients/<name>/progress")
    def add_progress(name):
        if find_client(name) is None:
            return error("Client not found", 404)
        data = request.get_json(silent=True) or {}
        week = data.get("week")
        if not week:
            return error("Week is required")
        try:
            adherence = validate_adherence(data.get("adherence"))
        except ValueError as exc:
            return error(str(exc))
        db = get_db()
        db.execute(
            "INSERT INTO progress (client_name, week, adherence)"
            " VALUES (?, ?, ?)", (name, week, adherence))
        db.commit()
        return jsonify({"client": name, "week": week,
                        "adherence": adherence}), 201

    @app.get("/clients/<name>/progress")
    def get_progress(name):
        if find_client(name) is None:
            return error("Client not found", 404)
        rows = get_db().execute(
            "SELECT week, adherence FROM progress WHERE client_name = ?"
            " ORDER BY id", (name,)).fetchall()
        return jsonify([dict(r) for r in rows])

    # ---------------- Workouts ----------------
    @app.post("/clients/<name>/workouts")
    def add_workout(name):
        if find_client(name) is None:
            return error("Client not found", 404)
        data = request.get_json(silent=True) or {}
        workout_type = data.get("workout_type")
        if workout_type not in WORKOUT_TYPES:
            return error(f"workout_type must be one of {WORKOUT_TYPES}")
        if not data.get("date"):
            return error("Date is required (YYYY-MM-DD)")
        db = get_db()
        db.execute(
            "INSERT INTO workouts (client_name, date, workout_type,"
            " duration_min, notes) VALUES (?, ?, ?, ?, ?)",
            (name, data["date"], workout_type,
             data.get("duration_min", 60), data.get("notes", "")))
        db.commit()
        return jsonify({"client": name, "workout_type": workout_type}), 201

    @app.get("/clients/<name>/workouts")
    def get_workouts(name):
        if find_client(name) is None:
            return error("Client not found", 404)
        rows = get_db().execute(
            "SELECT date, workout_type, duration_min, notes FROM workouts"
            " WHERE client_name = ? ORDER BY date DESC", (name,)).fetchall()
        return jsonify([dict(r) for r in rows])

    # ---------------- Program generator (from v3.x) ----------------
    @app.post("/clients/<name>/generate-program")
    def generate_program(name):
        client = find_client(name)
        if client is None:
            return error("Client not found", 404)
        plan = random.choice(PROGRAM_TEMPLATES[client["program"]])
        return jsonify({"client": name, "program": client["program"],
                        "suggested_plan": plan})

    return app


# Used by gunicorn inside Docker: `gunicorn app:app`
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

