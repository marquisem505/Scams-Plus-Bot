import sqlite3

DB_FILE = "scamsclub.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            rank TEXT DEFAULT 'Lookout',
            learning_path TEXT,
            experience TEXT,
            interest TEXT
        )
    ''')

    conn.commit()
    conn.close()

def create_user_if_not_exists(user_id, username, first_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if c.fetchone() is None:
        c.execute('INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)',
                  (user_id, username, first_name))
        conn.commit()

    conn.close()

def set_user_rank(user_id, rank):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE users SET rank = ? WHERE user_id = ?', (rank, user_id))
    conn.commit()
    conn.close()

def get_user_rank(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT rank FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def update_onboarding(user_id, learning_path=None, experience=None, interest=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if learning_path:
        c.execute('UPDATE users SET learning_path = ? WHERE user_id = ?', (learning_path, user_id))
    if experience:
        c.execute('UPDATE users SET experience = ? WHERE user_id = ?', (experience, user_id))
    if interest:
        c.execute('UPDATE users SET interest = ? WHERE user_id = ?', (interest, user_id))
    conn.commit()
    conn.close()

def get_onboarding_summary(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT username, first_name, learning_path, experience, interest FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "username": row[0] or "N/A",
            "first_name": row[1] or "N/A",
            "learning_path": row[2] or "N/A",
            "experience": row[3] or "N/A",
            "interest": row[4] or "N/A"
        }
    else:
        return {}
