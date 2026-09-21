from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or os.urandom(32)

DATABASE = os.path.join("data", "tasks.db")


# ============================================================
# BAZA DANYCH
# ============================================================

def get_db():
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs("data", exist_ok=True)

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            type TEXT DEFAULT 'daily',
            duration_days INTEGER,

            priority TEXT DEFAULT 'normal',
            category TEXT DEFAULT '',
            color TEXT DEFAULT '#3b82f6',

            due_time TEXT,
            deadline TEXT,

            reminder_enabled INTEGER DEFAULT 0,
            reminder_minutes INTEGER DEFAULT 15,

            created_timestamp TEXT
        )
    """)

    task_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
    }
    task_migrations = {
        "priority": "TEXT DEFAULT 'normal'",
        "category": "TEXT DEFAULT ''",
        "color": "TEXT DEFAULT '#3b82f6'",
        "due_time": "TEXT",
        "deadline": "TEXT",
        "reminder_enabled": "INTEGER DEFAULT 0",
        "reminder_minutes": "INTEGER DEFAULT 15",
        "created_timestamp": "TEXT",
        "user_id": "INTEGER REFERENCES users(id)"
    }
    for column_name, column_definition in task_migrations.items():
        if column_name not in task_columns:
            conn.execute(
                f"ALTER TABLE tasks ADD COLUMN {column_name} {column_definition}"
            )

    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,

            UNIQUE(task_id, date),

            FOREIGN KEY(task_id)
                REFERENCES tasks(id)
                ON DELETE CASCADE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS pause_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,

            FOREIGN KEY(task_id)
                REFERENCES tasks(id)
                ON DELETE CASCADE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT '',
            content TEXT NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    note_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(notes)").fetchall()
    }
    note_migrations = {
        "user_id": "INTEGER REFERENCES users(id)",
        "is_pinned": "INTEGER DEFAULT 0"
    }
    for column_name, column_definition in note_migrations.items():
        if column_name not in note_columns:
            conn.execute(
                f"ALTER TABLE notes ADD COLUMN {column_name} {column_definition}"
            )

    conn.commit()
    conn.close()


def current_user_id():
    return session.get("user_id")


def current_user():
    user_id = current_user_id()
    if not user_id:
        return None

    conn = get_db()
    user = conn.execute(
        "SELECT id, username FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return user


def task_belongs_to_user(conn, task_id):
    return conn.execute("""
        SELECT 1 FROM tasks WHERE id = ? AND user_id = ?
    """, (task_id, current_user_id())).fetchone() is not None


@app.before_request
def require_login():
    public_endpoints = {"login", "register", "static"}
    if request.endpoint in public_endpoints:
        return None
    if not current_user_id():
        return redirect(url_for("login", next=request.path))
    return None


@app.context_processor
def inject_current_user():
    return {"current_user": current_user()}


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user_id():
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            next_url = request.args.get("next") or request.form.get("next")
            if (
                not next_url
                or not next_url.startswith("/")
                or next_url.startswith("//")
            ):
                next_url = url_for("index")
            return redirect(next_url)

        flash("Nieprawidłowy login lub hasło.", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user_id():
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_confirmation = request.form.get("password_confirmation", "")

        if len(username) < 3 or len(username) > 40:
            flash("Login musi mieć od 3 do 40 znaków.", "error")
        elif len(password) < 8:
            flash("Hasło musi mieć co najmniej 8 znaków.", "error")
        elif password != password_confirmation:
            flash("Hasła nie są identyczne.", "error")
        else:
            conn = get_db()
            try:
                cursor = conn.execute("""
                    INSERT INTO users (username, password_hash, created_at)
                    VALUES (?, ?, ?)
                """, (
                    username,
                    generate_password_hash(password),
                    datetime.now().isoformat()
                ))
                user_id = cursor.lastrowid
                existing_users = conn.execute(
                    "SELECT COUNT(*) FROM users"
                ).fetchone()[0]
                if existing_users == 1:
                    conn.execute(
                        "UPDATE tasks SET user_id = ? WHERE user_id IS NULL",
                        (user_id,)
                    )
                    conn.execute(
                        "UPDATE notes SET user_id = ? WHERE user_id IS NULL",
                        (user_id,)
                    )
                conn.commit()
            except sqlite3.IntegrityError:
                conn.rollback()
                user_id = None
            finally:
                conn.close()

            if user_id:
                session["user_id"] = user_id
                return redirect(url_for("index"))
            flash("Ten login jest już zajęty.", "error")

    return render_template("register.html")


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ============================================================
# POMOCNICZE
# ============================================================

def today_string():
    return datetime.now().strftime("%Y-%m-%d")


def get_task_history(conn, selected_date):
    rows = conn.execute("""
        SELECT task_id, status
        FROM task_history
        JOIN tasks ON tasks.id = task_history.task_id
        WHERE task_history.date = ?
        AND tasks.user_id = ?
    """, (selected_date, current_user_id())).fetchall()

    return {
        str(row["task_id"]): row["status"]
        for row in rows
    }


def calculate_streak(conn, task_id, current_date_str):
    """
    Liczy serię poprzednich dni.
    Jeśli dzisiaj zadanie jest wykonane, seria obejmuje również dzisiaj.
    """

    current_date = datetime.strptime(
        current_date_str,
        "%Y-%m-%d"
    ).date()

    streak = 0

    # Najpierw sprawdzamy aktualny dzień
    row = conn.execute("""
        SELECT status
        FROM task_history
        WHERE task_id = ?
        AND date = ?
    """, (task_id, current_date_str)).fetchone()

    if row and row["status"] == "completed":
        streak += 1

    current_date -= timedelta(days=1)

    while True:
        date_str = current_date.strftime("%Y-%m-%d")

        row = conn.execute("""
            SELECT status
            FROM task_history
            WHERE task_id = ?
            AND date = ?
        """, (task_id, date_str)).fetchone()

        if not row or row["status"] != "completed":
            break

        streak += 1
        current_date -= timedelta(days=1)

    return streak


def is_task_paused(conn, task_id, selected_date):
    row = conn.execute("""
        SELECT start_date, end_date
        FROM pause_periods
        WHERE task_id = ?
        AND start_date <= ?
        AND (end_date IS NULL OR ? < end_date)
        ORDER BY start_date DESC
        LIMIT 1
    """, (task_id, selected_date, selected_date)).fetchone()

    return row


def task_should_exist_on_date(task, selected_date, history_exists):
    created_at = task["created_at"]

    if created_at > selected_date:
        return False

    task_type = task["type"]

    if task_type == "daily":
        return True

    if task_type == "once":
        return (
            created_at == selected_date
            or history_exists
        )

    if task_type == "for_x_days":
        duration = task["duration_days"] or 1

        created_dt = datetime.strptime(
            created_at,
            "%Y-%m-%d"
        ).date()

        selected_dt = datetime.strptime(
            selected_date,
            "%Y-%m-%d"
        ).date()

        end_dt = created_dt + timedelta(
            days=duration - 1
        )

        return (
            created_dt <= selected_dt <= end_dt
            or history_exists
        )

    return False


# ============================================================
# STRONA GŁÓWNA
# ============================================================

@app.route("/")
def index():

    selected_date = request.args.get(
        "date",
        today_string()
    )

    try:
        selected_dt = datetime.strptime(
            selected_date,
            "%Y-%m-%d"
        )
    except ValueError:
        selected_date = today_string()
        selected_dt = datetime.strptime(
            selected_date,
            "%Y-%m-%d"
        )

    yesterday = (
        selected_dt - timedelta(days=1)
    ).strftime("%Y-%m-%d")

    tomorrow = (
        selected_dt + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    today = today_string()

    conn = get_db()

    tasks_rows = conn.execute("""
        SELECT *
        FROM tasks
        WHERE user_id = ?
        ORDER BY
            CASE priority
                WHEN 'high' THEN 1
                WHEN 'normal' THEN 2
                WHEN 'low' THEN 3
                ELSE 4
            END,
                id
            """, (current_user_id(),)).fetchall()

    current_history = get_task_history(
        conn,
        selected_date
    )

    active_tasks = []
    paused_tasks = []

    for task in tasks_rows:

        task_id = task["id"]

        history_exists = str(task_id) in current_history

        if not task_should_exist_on_date(
            task,
            selected_date,
            history_exists
        ):
            continue

        pause = is_task_paused(
            conn,
            task_id,
            selected_date
        )

        task_data = dict(task)

        task_data["status"] = current_history.get(
            str(task_id),
            "pending"
        )

        task_data["streak"] = calculate_streak(
            conn,
            task_id,
            selected_date
        )

        if pause:
            task_data["current_pause_start"] = pause[
                "start_date"
            ]

            paused_tasks.append(task_data)
        else:
            active_tasks.append(task_data)

    # ========================================================
    # WYKRES 7 DNI
    # ========================================================

    week_days = []

    for i in range(-3, 4):

        day_dt = selected_dt + timedelta(days=i)

        date_str = day_dt.strftime("%Y-%m-%d")

        rows = conn.execute("""
            SELECT status
            FROM task_history
            JOIN tasks ON tasks.id = task_history.task_id
            WHERE task_history.date = ?
            AND tasks.user_id = ?
        """, (date_str, current_user_id())).fetchall()

        done = sum(
            1 for r in rows
            if r["status"] == "completed"
        )

        failed = sum(
            1 for r in rows
            if r["status"] == "failed"
        )

        total = len(rows)

        percentage = (
            round(
                ((done - failed) / total) * 100
            )
            if total
            else 0
        )

        polish_days = [
            "Pn",
            "Wt",
            "Śr",
            "Cz",
            "Pt",
            "Sob",
            "Nie"
        ]

        week_days.append({
            "date": date_str,
            "day_num": day_dt.strftime("%d.%m"),
            "label": polish_days[
                day_dt.weekday()
            ],
            "percentage": percentage,
            "done": done,
            "failed": failed,
            "total": total,
            "is_selected": (
                date_str == selected_date
            )
        })

    # ========================================================
    # STATYSTYKI
    # ========================================================

    month_prefix = selected_date[:7]

    month_rows = conn.execute("""
        SELECT status
        FROM task_history
        JOIN tasks ON tasks.id = task_history.task_id
        WHERE task_history.date LIKE ?
        AND tasks.user_id = ?
    """, (month_prefix + "%", current_user_id())).fetchall()

    month_done = sum(
        1 for r in month_rows
        if r["status"] == "completed"
    )

    month_failed = sum(
        1 for r in month_rows
        if r["status"] == "failed"
    )

    month_total = len(month_rows)

    month_percentage = (
        round(
            ((month_done - month_failed)
             / month_total) * 100
        )
        if month_total
        else 0
    )

    all_time_done = conn.execute("""
        SELECT COUNT(*)
        FROM task_history
        JOIN tasks ON tasks.id = task_history.task_id
        WHERE task_history.status = 'completed'
        AND tasks.user_id = ?
    """, (current_user_id(),)).fetchone()[0]

    history_rows = conn.execute("""
        SELECT date, task_id, status
        FROM task_history
        JOIN tasks ON tasks.id = task_history.task_id
        WHERE tasks.user_id = ?
        ORDER BY date DESC, task_id
    """, (current_user_id(),)).fetchall()

    history = {}
    for row in history_rows:
        history.setdefault(row["date"], {})[
            str(row["task_id"])
        ] = row["status"]

    stats = {
        "month_done": month_done,
        "month_failed": month_failed,
        "month_total": month_total,
        "month_percentage": month_percentage,
        "all_time_done": all_time_done
    }

    # ========================================================
    # NOTATKI
    # ========================================================

    notes = conn.execute("""
        SELECT *
        FROM notes
        WHERE date = ?
        AND user_id = ?
        ORDER BY id DESC
    """, (selected_date, current_user_id())).fetchall()

    pinned_notes = conn.execute("""
        SELECT *
        FROM notes
        WHERE user_id = ? AND is_pinned = 1
        ORDER BY updated_at DESC, id DESC
    """, (current_user_id(),)).fetchall()

    # ========================================================
    # DANE DO KALENDARZA
    # ========================================================

    task_days_rows = conn.execute("""
        SELECT DISTINCT created_at
        FROM tasks
        WHERE type = 'once'
        AND user_id = ?
    """, (current_user_id(),)).fetchall()

    once_task_days = [
        row["created_at"]
        for row in task_days_rows
    ]

    conn.close()

    return render_template(
        "dashboard.html",
        tasks=active_tasks,
        paused_tasks=paused_tasks,
        selected_date=selected_date,
        today_date=today,
        yesterday_date=yesterday,
        tomorrow_date=tomorrow,
        week_days=week_days,
        stats=stats,
        notes=notes,
        pinned_notes=pinned_notes,
        once_task_days=once_task_days,
        history=history,
        all_tasks=tasks_rows
    )


def get_selected_date():
    selected_date = request.args.get("date", today_string())
    try:
        datetime.strptime(selected_date, "%Y-%m-%d")
    except ValueError:
        selected_date = today_string()
    return selected_date


def get_ordered_tasks(conn):
    return conn.execute("""
        SELECT *
        FROM tasks
        WHERE user_id = ?
        ORDER BY
            CASE priority
                WHEN 'high' THEN 1
                WHEN 'normal' THEN 2
                WHEN 'low' THEN 3
                ELSE 4
            END,
                id
            """, (current_user_id(),)).fetchall()


def get_tasks_for_date(conn, selected_date):
    task_rows = get_ordered_tasks(conn)
    current_history = get_task_history(conn, selected_date)
    active_tasks = []
    paused_tasks = []

    for task in task_rows:
        task_id = task["id"]
        if not task_should_exist_on_date(
            task,
            selected_date,
            str(task_id) in current_history
        ):
            continue

        task_data = dict(task)
        task_data["status"] = current_history.get(str(task_id), "pending")
        task_data["streak"] = calculate_streak(conn, task_id, selected_date)
        pause = is_task_paused(conn, task_id, selected_date)

        if pause:
            task_data["current_pause_start"] = pause["start_date"]
            paused_tasks.append(task_data)
        else:
            active_tasks.append(task_data)

    return active_tasks, paused_tasks


def section_context(selected_date):
    selected_dt = datetime.strptime(selected_date, "%Y-%m-%d")
    conn = get_db()
    tasks, paused_tasks = get_tasks_for_date(conn, selected_date)
    notes = conn.execute("""
        SELECT * FROM notes
        WHERE date = ? AND user_id = ?
        ORDER BY id DESC
    """, (selected_date, current_user_id())).fetchall()
    pinned_notes = conn.execute("""
        SELECT * FROM notes
        WHERE user_id = ? AND is_pinned = 1
        ORDER BY updated_at DESC, id DESC
    """, (current_user_id(),)).fetchall()
    once_task_days = [
        row["created_at"] for row in conn.execute("""
            SELECT DISTINCT created_at FROM tasks WHERE type = 'once'
            AND user_id = ?
        """, (current_user_id(),)).fetchall()
    ]
    all_tasks = get_ordered_tasks(conn)
    history_rows = conn.execute("""
        SELECT task_history.date, task_history.task_id, task_history.status
        FROM task_history
        JOIN tasks ON tasks.id = task_history.task_id
        WHERE tasks.user_id = ?
        ORDER BY task_history.date DESC, task_history.task_id
    """, (current_user_id(),)).fetchall()
    history = {}
    for row in history_rows:
        history.setdefault(row["date"], {})[str(row["task_id"])] = row["status"]

    polish_days = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nie"]
    upcoming_week = []
    for offset in range(1, 8):
        day = selected_dt + timedelta(days=offset)
        date_str = day.strftime("%Y-%m-%d")
        day_tasks, _ = get_tasks_for_date(conn, date_str)
        upcoming_week.append({
            "date": date_str,
            "label": polish_days[day.weekday()],
            "day_num": day.strftime("%d.%m"),
            "tasks": day_tasks
        })

    month_start = selected_dt.replace(day=1)
    if month_start.month == 12:
        next_month = month_start.replace(
            year=month_start.year + 1,
            month=1
        )
    else:
        next_month = month_start.replace(month=month_start.month + 1)

    calendar_days = []
    for offset in range((next_month - month_start).days):
        day = month_start + timedelta(days=offset)
        date_str = day.strftime("%Y-%m-%d")
        day_tasks, _ = get_tasks_for_date(conn, date_str)
        calendar_days.append({
            "date": date_str,
            "day": day.day,
            "tasks": [
                {
                    "title": task["title"],
                    "color": task["color"] or "#397da9",
                    "status": task["status"]
                }
                for task in day_tasks
            ],
            "is_selected": date_str == selected_date,
            "is_today": date_str == today_string()
        })
    polish_months = [
        "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
        "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"
    ]
    previous_month_date = (month_start - timedelta(days=1)).strftime("%Y-%m-%d")
    next_month_date = next_month.strftime("%Y-%m-%d")
    conn.close()

    return {
        "selected_date": selected_date,
        "today_date": today_string(),
        "yesterday_date": (selected_dt - timedelta(days=1)).strftime("%Y-%m-%d"),
        "tomorrow_date": (selected_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
        "tasks": tasks,
        "paused_tasks": paused_tasks,
        "notes": notes,
        "pinned_notes": pinned_notes,
        "once_task_days": once_task_days,
        "all_tasks": all_tasks,
        "history": history,
        "week_days": [],
        "upcoming_week": upcoming_week,
        "calendar_days": calendar_days,
        "calendar_month": f"{polish_months[month_start.month - 1]} {month_start.year}",
        "calendar_leading": month_start.weekday(),
        "previous_month_date": previous_month_date,
        "next_month_date": next_month_date
    }


@app.route("/tasks")
def tasks_page():
    return render_template("tasks.html", **section_context(get_selected_date()))


@app.route("/calendar")
def calendar_page():
    return render_template("calendar.html", **section_context(get_selected_date()))


@app.route("/notes")
def notes_page():
    return render_template("notes.html", **section_context(get_selected_date()))


@app.route("/history")
def history_page():
    return render_template("history.html", **section_context(get_selected_date()))


# ============================================================
# DODAWANIE ZADANIA
# ============================================================

@app.route("/add", methods=["POST"])
def add_task():

    title = request.form.get(
        "title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    task_type = request.form.get(
        "type",
        "daily"
    )

    duration_days = request.form.get(
        "duration_days",
        "1"
    )

    selected_date = request.form.get(
        "selected_date",
        today_string()
    )

    priority = request.form.get(
        "priority",
        "normal"
    )

    category = request.form.get(
        "category",
        ""
    ).strip()

    color = request.form.get(
        "color",
        "#3b82f6"
    )

    due_time = request.form.get(
        "due_time"
    ) or None

    deadline = request.form.get(
        "deadline"
    ) or None

    reminder_enabled = (
        1
        if request.form.get("reminder_enabled")
        else 0
    )

    reminder_minutes = request.form.get(
        "reminder_minutes",
        "15"
    )

    try:
        reminder_minutes = int(
            reminder_minutes
        )
    except ValueError:
        reminder_minutes = 15

    if title:

        conn = get_db()

        conn.execute("""
            INSERT INTO tasks (
                title,
                description,
                created_at,
                type,
                duration_days,
                priority,
                category,
                color,
                due_time,
                deadline,
                reminder_enabled,
                reminder_minutes,
                created_timestamp,
                user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            selected_date,
            task_type,
            int(duration_days)
                if task_type == "for_x_days"
                else None,
            priority,
            category,
            color,
            due_time,
            deadline,
            reminder_enabled,
            reminder_minutes,
            datetime.now().isoformat(),
            current_user_id()
        ))

        conn.commit()
        conn.close()

    return redirect(
        url_for(
            "index",
            date=selected_date
        )
    )


# ============================================================
# EDYCJA ZADANIA
# ============================================================

@app.route(
    "/edit_task/<int:task_id>",
    methods=["POST"]
)
def edit_task(task_id):

    selected_date = request.form.get(
        "selected_date",
        today_string()
    )

    title = request.form.get(
        "title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    priority = request.form.get(
        "priority",
        "normal"
    )

    category = request.form.get(
        "category",
        ""
    ).strip()

    color = request.form.get(
        "color",
        "#3b82f6"
    )

    due_time = request.form.get(
        "due_time"
    ) or None

    deadline = request.form.get(
        "deadline"
    ) or None

    reminder_enabled = (
        1
        if request.form.get("reminder_enabled")
        else 0
    )

    reminder_minutes = request.form.get(
        "reminder_minutes",
        "15"
    )

    try:
        reminder_minutes = int(
            reminder_minutes
        )
    except ValueError:
        reminder_minutes = 15

    if title:

        conn = get_db()

        if not task_belongs_to_user(conn, task_id):
            conn.close()
            return redirect(url_for("tasks_page", date=selected_date))

        conn.execute("""
            UPDATE tasks
            SET
                title = ?,
                description = ?,
                priority = ?,
                category = ?,
                color = ?,
                due_time = ?,
                deadline = ?,
                reminder_enabled = ?,
                reminder_minutes = ?
            WHERE id = ? AND user_id = ?
        """, (
            title,
            description,
            priority,
            category,
            color,
            due_time,
            deadline,
            reminder_enabled,
            reminder_minutes,
            task_id,
            current_user_id()
        ))

        conn.commit()
        conn.close()

    return redirect(
        url_for(
            "index",
            date=selected_date
        )
    )


# ============================================================
# STATUS ZADANIA
# ============================================================

@app.route(
    "/update_status",
    methods=["POST"]
)
def update_status():

    task_id = request.form.get(
        "task_id"
    )

    status = request.form.get(
        "status"
    )

    selected_date = request.form.get(
        "selected_date",
        today_string()
    )

    status_map = {
        "done": "completed",
        "completed": "completed",
        "not_done": "failed",
        "failed": "failed",
        "pending": "pending"
    }

    status = status_map.get(
        status,
        "pending"
    )

    conn = get_db()

    if not task_belongs_to_user(conn, task_id):
        conn.close()
        return redirect(url_for("tasks_page", date=selected_date))

    if status == "pending":

        conn.execute("""
            DELETE FROM task_history
            WHERE task_id = ?
            AND date = ?
        """, (
            task_id,
            selected_date
        ))

    else:

        conn.execute("""
            INSERT INTO task_history (
                task_id,
                date,
                status
            )
            VALUES (?, ?, ?)
            ON CONFLICT(task_id, date)
            DO UPDATE SET status = excluded.status
        """, (
            task_id,
            selected_date,
            status
        ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "index",
            date=selected_date
        )
    )


# ============================================================
# PAUZA
# ============================================================

@app.route(
    "/pause_task/<int:task_id>",
    methods=["POST"]
)
def pause_task(task_id):

    selected_date = request.form.get(
        "selected_date",
        today_string()
    )

    conn = get_db()

    if not task_belongs_to_user(conn, task_id):
        conn.close()
        return redirect(url_for("tasks_page", date=selected_date))

    existing = conn.execute("""
        SELECT id
        FROM pause_periods
        WHERE task_id = ?
        AND start_date <= ?
        AND end_date IS NULL
        LIMIT 1
    """, (
        task_id,
        selected_date
    )).fetchone()

    if not existing:

        conn.execute("""
            INSERT INTO pause_periods (
                task_id,
                start_date,
                end_date
            )
            VALUES (?, ?, NULL)
        """, (
            task_id,
            selected_date
        ))

        conn.commit()

    conn.close()

    return redirect(
        url_for(
            "index",
            date=selected_date
        )
    )


# ============================================================
# WZNOWIENIE
# ============================================================

@app.route(
    "/resume_task/<int:task_id>",
    methods=["POST"]
)
def resume_task(task_id):

    selected_date = request.form.get(
        "selected_date",
        today_string()
    )

    conn = get_db()

    if not task_belongs_to_user(conn, task_id):
        conn.close()
        return redirect(url_for("tasks_page", date=selected_date))

    conn.execute("""
        UPDATE pause_periods
        SET end_date = ?
        WHERE task_id = ?
        AND end_date IS NULL
    """, (
        selected_date,
        task_id
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "index",
            date=selected_date
        )
    )


# ============================================================
# USUWANIE ZADANIA
# ============================================================

@app.route(
    "/delete/<int:task_id>",
    methods=["POST"]
)
def delete_task(task_id):

    selected_date = request.form.get(
        "selected_date",
        today_string()
    )

    conn = get_db()

    if not task_belongs_to_user(conn, task_id):
        conn.close()
        return redirect(url_for("tasks_page", date=selected_date))

    conn.execute("""
        DELETE FROM tasks
        WHERE id = ? AND user_id = ?
    """, (task_id, current_user_id()))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "index",
            date=selected_date
        )
    )


# ============================================================
# NOTATKI
# ============================================================

@app.route(
    "/add_note",
    methods=["POST"]
)
def add_note():

    selected_date = request.form.get(
        "selected_date",
        today_string()
    )

    title = request.form.get(
        "title",
        ""
    ).strip()

    content = request.form.get(
        "content",
        ""
    ).strip()

    if content:

        now = datetime.now().isoformat()

        conn = get_db()

        conn.execute("""
            INSERT INTO notes (
                title,
                content,
                date,
                created_at,
                updated_at,
                user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title,
            content,
            selected_date,
            now,
            now,
            current_user_id()
        ))

        conn.commit()
        conn.close()

    return redirect(
        url_for(
            "notes_page",
            date=selected_date
        )
    )


@app.route("/edit_note/<int:note_id>", methods=["POST"])
def edit_note(note_id):
    selected_date = request.form.get("selected_date", today_string())
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()

    if content:
        conn = get_db()
        conn.execute("""
            UPDATE notes
            SET title = ?, content = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (
            title,
            content,
            datetime.now().isoformat(),
            note_id,
            current_user_id()
        ))
        conn.commit()
        conn.close()

    return redirect(url_for("notes_page", date=selected_date))


@app.route("/toggle_note_pin/<int:note_id>", methods=["POST"])
def toggle_note_pin(note_id):
    selected_date = request.form.get("selected_date", today_string())
    conn = get_db()
    conn.execute("""
        UPDATE notes
        SET is_pinned = CASE WHEN is_pinned = 1 THEN 0 ELSE 1 END,
            updated_at = ?
        WHERE id = ? AND user_id = ?
    """, (datetime.now().isoformat(), note_id, current_user_id()))
    conn.commit()
    conn.close()
    return redirect(url_for("notes_page", date=selected_date))


@app.route(
    "/delete_note/<int:note_id>",
    methods=["POST"]
)
def delete_note(note_id):

    selected_date = request.form.get(
        "selected_date",
        today_string()
    )

    conn = get_db()

    conn.execute("""
        DELETE FROM notes
        WHERE id = ? AND user_id = ?
    """, (note_id, current_user_id()))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "notes_page",
            date=selected_date
        )
    )


# ============================================================
# API - PRZYPOMNIENIA
# ============================================================

@app.route("/api/reminders")
def reminders():

    selected_date = request.args.get(
        "date",
        today_string()
    )

    conn = get_db()

    rows = conn.execute("""
        SELECT
            id,
            title,
            due_time,
            reminder_minutes,
            color,
            priority
        FROM tasks
        WHERE created_at <= ?
        AND user_id = ?
        AND reminder_enabled = 1
        AND due_time IS NOT NULL
    """, (selected_date, current_user_id())).fetchall()

    result = []

    for row in rows:

        result.append({
            "id": row["id"],
            "title": row["title"],
            "due_time": row["due_time"],
            "reminder_minutes": row[
                "reminder_minutes"
            ],
            "color": row["color"],
            "priority": row["priority"]
        })

    conn.close()

    return jsonify(result)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    init_db()

    app.run(
        debug=True
    )
