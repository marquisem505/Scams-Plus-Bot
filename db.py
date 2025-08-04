import sqlite3

DB_FILE = "scamsclub.sqlite"

# --- Init ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
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

# --- Create if doesn't exist ---
def create_user_if_not_exists(user_id, username, first_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    if c.fetchone() is None:
        c.execute('INSERT INTO users (id, username, first_name) VALUES (?, ?, ?)',
                  (user_id, username, first_name))
    conn.commit()
    conn.close()

# --- Set rank ---
def set_user_rank(user_id, rank):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE users SET rank = ? WHERE id = ?', (rank, user_id))
    conn.commit()
    conn.close()

# --- Get rank ---
def get_user_rank(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT rank FROM users WHERE id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# --- Onboarding Update ---
def update_onboarding(user_id, learning_path=None, experience=None, interest=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if learning_path:
        c.execute('UPDATE users SET learning_path = ? WHERE id = ?', (learning_path, user_id))
    if experience:
        c.execute('UPDATE users SET experience = ? WHERE id = ?', (experience, user_id))
    if interest:
        c.execute('UPDATE users SET interest = ? WHERE id = ?', (interest, user_id))
    conn.commit()
    conn.close()

# --- Get Summary ---
def get_onboarding_summary(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT username, first_name, learning_path, experience, interest FROM users WHERE id = ?', (user_id,))
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
    return {}
    
# --- Get User ID by Username ---
def get_user_id_by_username(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None
