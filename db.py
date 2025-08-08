import os
import sqlite3

DB_FILE = os.getenv("DB_FILE", "scamsclub.sqlite")

# --- Init ---
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                rank TEXT DEFAULT 'Lookout',
                learning_path TEXT,
                experience TEXT,
                interest TEXT
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"❌ Error initializing DB: {e}")
    finally:
        conn.close()

# --- Create if doesn't exist ---
def create_user_if_not_exists(user_id, username, first_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if c.fetchone() is None:
        c.execute(
            "INSERT INTO users (id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name),
        )
    else:
        c.execute(
            "UPDATE users SET username = ?, first_name = ? WHERE id = ?",
            (username, first_name, user_id),
        )
    conn.commit()
    conn.close()

# --- Set user rank ---
def set_user_rank(user_id, rank):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET rank = ? WHERE id = ?", (rank, user_id))
    conn.commit()
    conn.close()

# --- Get rank (single user) ---
def get_user_rank(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT rank FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# --- Count users by rank ---
def get_user_count_by_rank():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT COALESCE(rank, 'Unranked') AS r, COUNT(*)
        FROM users
        GROUP BY r
    """)
    rows = c.fetchall()
    conn.close()
    return dict(rows)

# --- Update onboarding fields ---
def update_onboarding(user_id, learning_path=None, experience=None, interest=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if learning_path is not None:
        c.execute("UPDATE users SET learning_path = ? WHERE id = ?", (learning_path, user_id))
    if experience is not None:
        c.execute("UPDATE users SET experience = ? WHERE id = ?", (experience, user_id))
    if interest is not None:
        c.execute("UPDATE users SET interest = ? WHERE id = ?", (interest, user_id))
    conn.commit()
    conn.close()

# --- Fetch full onboarding summary ---
def get_onboarding_summary(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT username, first_name, learning_path, experience, interest
        FROM users WHERE id = ?
    """, (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "username": row[0],
            "first_name": row[1],
            "learning_path": row[2],
            "experience": row[3],
            "interest": row[4],
        }
    return {}

# --- Get User ID by Username ---
def get_user_id_by_username(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# --- Get All Users ---
def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, username, first_name FROM users ORDER BY id")
    users = c.fetchall()
    conn.close()
    return users