import sqlite3

def init_db():
    conn = sqlite3.connect("scamsclub.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            rank TEXT,
            experience TEXT,
            interest TEXT,
            learning_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

def set_user_rank(user_id, rank):
    conn = sqlite3.connect("scamsclub.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (user_id, rank)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET rank=excluded.rank
    ''', (user_id, rank))
    conn.commit()
    conn.close()

def get_user_rank(user_id):
    conn = sqlite3.connect("scamsclub.db")
    c = conn.cursor()
    c.execute('SELECT rank FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def update_onboarding(user_id, **kwargs):
    conn = sqlite3.connect("scamsclub.db")
    c = conn.cursor()
    for key, value in kwargs.items():
        c.execute(f'''
            UPDATE users SET {key} = ? WHERE user_id = ?
        ''', (value, user_id))
    conn.commit()
    conn.close()

def create_user_if_not_exists(user_id, username, first_name):
    conn = sqlite3.connect("scamsclub.db")
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
    ''', (user_id, username, first_name))
    conn.commit()
    conn.close()

def get_onboarding_summary(user_id):
    conn = sqlite3.connect("scamsclub.db")
    c = conn.cursor()
    c.execute('''
        SELECT username, first_name, learning_path, experience, interest
        FROM users WHERE user_id = ?
    ''', (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "username": row[0],
            "first_name": row[1],
            "learning_path": row[2],
            "experience": row[3],
            "interest": row[4]
        }
    return None
