import sqlite3

# -----------------------------
# Connect to database
# -----------------------------
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# -----------------------------
# Users table
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT
)
""")

# -----------------------------
# Chat history table
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,       -- student1, student2, etc.
    sender TEXT,         -- "user" or "bot"
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# -----------------------------
# Emoji reactions table
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    message TEXT,
    emoji TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# -----------------------------
# Insert demo users
# -----------------------------
password = "1234"
students = [
    "student01@test.com", "student02@test.com", "student03@test.com",
    "student04@test.com", "student05@test.com", "student06@test.com",
    "student07@test.com", "student08@test.com", "student09@test.com",
    "student10@test.com", "student11@test.com", "student12@test.com",
    "student13@test.com", "student14@test.com", "student15@test.com",
    "student16@test.com", "student17@test.com", "student18@test.com",
    "student19@test.com", "student20@test.com", "student21@test.com",
    "student22@test.com", "student23@test.com", "student24@test.com",
    "student25@test.com", "student26@test.com", "student27@test.com",
    "student28@test.com", "student29@test.com", "student30@test.com"
]

for email in students:
    cursor.execute(
        "INSERT OR IGNORE INTO users (email, password) VALUES (?, ?)",
        (email, password)
    )

# -----------------------------
# Commit & close
# -----------------------------
conn.commit()
conn.close()

print("✅ Database ready: users, chat_history, reactions")
