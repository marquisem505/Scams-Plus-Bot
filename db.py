# db.py
import sqlite3

DB_PATH = "scamsclub.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_ranks (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            rank TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS onboarding (
            user_id INTEGER PRIMARY KEY,
            learning_path TEXT,
            experience TEXT,
            interest TEXT
        )
    ''')

    conn.commit()
    conn.close()

def create_user_if_not_exists(user_id, username, first_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user_ranks WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO user_ranks (user_id, username, first_name, rank) VALUES (?, ?, ?, ?)",
                       (user_id, username, first_name, "Lookout"))
        conn.commit()
    conn.close()

def set_user_rank(user_id, rank):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE user_ranks SET rank = ? WHERE user_id = ?", (rank, user_id))
    conn.commit()
    conn.close()

def get_user_rank(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT rank FROM user_ranks WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_onboarding(user_id, learning_path=None, experience=None, interest=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM onboarding WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()

    if not exists:
        cursor.execute("INSERT INTO onboarding (user_id, learning_path, experience, interest) VALUES (?, ?, ?, ?)",
                       (user_id, learning_path or "", experience or "", interest or ""))
    else:
        if learning_path:
            cursor.execute("UPDATE onboarding SET learning_path = ? WHERE user_id = ?", (learning_path, user_id))
        if experience:
            cursor.execute("UPDATE onboarding SET experience = ? WHERE user_id = ?", (experience, user_id))
        if interest:
            cursor.execute("UPDATE onboarding SET interest = ? WHERE user_id = ?", (interest, user_id))

    conn.commit()
    conn.close()

def get_onboarding_summary(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.first_name, r.username, o.learning_path, o.experience, o.interest
        FROM user_ranks r
        LEFT JOIN onboarding o ON r.user_id = o.user_id
        WHERE r.user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "first_name": result[0],
            "username": result[1],
            "learning_path": result[2],
            "experience": result[3],
            "interest": result[4]
        }
    return None
