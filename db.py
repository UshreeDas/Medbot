import sqlite3

conn = sqlite3.connect("chat.db", check_same_thread=False)
cursor = conn.cursor()

# USERS
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

# CHATS (linked to user)
cursor.execute("""
CREATE TABLE IF NOT EXISTS chats (
    chat_id TEXT PRIMARY KEY,
    username TEXT
)
""")

# MESSAGES
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    chat_id TEXT,
    role TEXT,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()


# -------------------------
# USER
# -------------------------
def register_user(username, password):
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
        (username, password)
    )
    conn.commit()

def login_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return cursor.fetchone() is not None


# -------------------------
# CHAT
# -------------------------
def create_chat(chat_id, username):
    cursor.execute("INSERT INTO chats VALUES (?, ?)", (chat_id, username))
    conn.commit()

def get_user_chats(username):
    cursor.execute("SELECT chat_id FROM chats WHERE username=?", (username,))
    return [row[0] for row in cursor.fetchall()]


# -------------------------
# MESSAGES
# -------------------------
def save_message(chat_id, role, message):
    cursor.execute(
        "INSERT INTO messages (chat_id, role, message) VALUES (?, ?, ?)",
        (chat_id, role, message)
    )
    conn.commit()
def load_chat(chat_id):
    cursor.execute("SELECT role, message FROM messages WHERE chat_id=?", (chat_id,))
    return cursor.fetchall()
# -------------------------
# RENAME CHAT
# -------------------------
def rename_chat(old_id, new_id):
    cursor.execute(
        "UPDATE chats SET chat_id=? WHERE chat_id=?",
        (new_id, old_id)
    )

    cursor.execute(
        "UPDATE messages SET chat_id=? WHERE chat_id=?",
        (new_id, old_id)
    )

    conn.commit()


# -------------------------
# DELETE CHAT
# -------------------------
def delete_chat(chat_id):
    cursor.execute(
        "DELETE FROM chats WHERE chat_id=?",
        (chat_id,)
    )

    cursor.execute(
        "DELETE FROM messages WHERE chat_id=?",
        (chat_id,)
    )

    conn.commit()