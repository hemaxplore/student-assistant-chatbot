from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import mysql.connector
import random
import time
from chatbot_core import predict_intent, get_response
from datetime import datetime

app = Flask(__name__)
app.secret_key = "student_assistant_secret_key"

# =========================
# SESSION FIX
# =========================
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)

# =========================
# MySQL CONFIG
# =========================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "student_assistant"
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# =========================
# INIT DATABASE
# =========================
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            sender ENUM('user','bot') NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            emoji VARCHAR(10) NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

# ✅ SAFE INIT (Render-friendly)
if __name__ != "__main__":
    init_db()

# =========================
# SAVE MESSAGE (DB + SESSION)
# =========================
def save_message(username, sender, message):
    now = datetime.now()   # ✅ FIX

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chat_history (username, sender, message, timestamp) VALUES (%s,%s,%s,%s)",
        (username, sender, message, now)
    )
    conn.commit()
    cur.close()
    conn.close()

    if "history" not in session:
        session["history"] = []

    session["history"].append({
        "sender": sender,
        "message": message,
        "time": now.strftime("%I:%M %p"),
        "date": now.strftime("%Y-%m-%d")
    })
    
# =========================
# LOAD MESSAGES FROM DB
# =========================
def load_messages(username):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT sender, message,
               DATE_FORMAT(timestamp, '%h:%i %p') AS time,
               DATE(timestamp) AS date
        FROM chat_history
        WHERE username=%s
        ORDER BY timestamp ASC
    """, (username,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# =========================
# LOGIN
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session.clear()
            session["user"] = email
            session["last_intent"] = None
            session["history"] = []
            return redirect(url_for("chat_page"))

        return render_template("login.html", error="❌ Invalid login")

    return render_template("login.html")

# =========================
# CHAT PAGE
# =========================
@app.route("/chatbot")
def chat_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", user=session["user"])

# =========================
# LOAD HISTORY API (FIXED)
# =========================
@app.route("/load_history")
def load_history():
    if "user" not in session:
        return jsonify({"history": []})

    username = session["user"]
    today = datetime.now().strftime("%Y-%m-%d")

    session_history = session.get("history", [])

    fixed = []
    for m in session_history:
        if "date" not in m:
            m["date"] = today
        if "time" not in m:
            m["time"] = ""
        fixed.append(m)

    if fixed:
        session["history"] = fixed
        return jsonify({"history": fixed})

    db_history = load_messages(username)
    session["history"] = db_history
    return jsonify({"history": db_history})

# =========================
# RULE-BASED INTENTS
# =========================
RULES = [
    {"intent": "greeting", "keywords": ["hi", "hello", "hey", "hai", "hii", "good morning", "good evening"]},
    {"intent": "goodbye", "keywords": ["bye", "goodbye", "see you", "exit chat"]},
    {"intent": "thanks", "keywords": ["thanks", "thank you", "appreciate"]},
    {"intent": "exam_info", "keywords": ["exam", "exam date", "exam schedule"]},
    {"intent": "exam_postponed", "keywords": ["exam postponed", "exam cancelled", "exam delayed"]},
    {"intent": "library_timings", "keywords": ["library timing", "library hours"]},
    {"intent": "fee_details", "keywords": ["fees", "college fees", "exam fees"]},
    {"intent": "scholarship_info", "keywords": ["scholarship"]}
]

# =========================
# CHAT API (WITH CONTEXT MEMORY)
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return jsonify({"response": "Please login first 🙂", "confidence": 0})

    data = request.get_json(force=True)
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"response": "Type something 😊", "confidence": 0})

    username = session["user"]
    save_message(username, "user", message)

    msg_lower = message.lower()

    for rule in RULES:
        if any(k in msg_lower for k in rule["keywords"]):
            reply = get_response(rule["intent"])
            session["last_intent"] = rule["intent"]
            save_message(username, "bot", reply)
            return jsonify({"response": reply, "confidence": 100})

    time.sleep(random.uniform(0.4, 0.8))
    intent, confidence = predict_intent(message)

    if confidence >= 0.35:
        reply = get_response(intent)
        session["last_intent"] = intent
        save_message(username, "bot", reply)
        return jsonify({"response": reply, "confidence": round(confidence * 100, 1)})

    last_intent = session.get("last_intent")
    if last_intent:
        reply = get_response(last_intent)
        save_message(username, "bot", reply)
        return jsonify({"response": reply, "confidence": 50})

    reply = "Hmm 🤔 I’m not sure. Can you rephrase?"
    save_message(username, "bot", reply)
    return jsonify({"response": reply, "confidence": 0})


# =========================
# SAVE EMOJI REACTION
# =========================
@app.route("/save_reaction", methods=["POST"])
def save_reaction():
    if "user" not in session:
        return jsonify({"status": "error"})

    data = request.get_json(force=True)
    user = session["user"]
    message = data.get("message")
    emoji = data.get("emoji")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM reactions WHERE user=%s AND message=%s", (user, message))
    cur.execute("INSERT INTO reactions (user, message, emoji) VALUES (%s,%s,%s)", (user, message, emoji))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok"})

# =========================
# LOAD EMOJI REACTION
# =========================
@app.route("/load_reaction")
def load_reaction():
    message = request.args.get("message")

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT emoji, COUNT(*) AS count
        FROM reactions
        WHERE message=%s
        GROUP BY emoji
    """, (message,))
    data = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(data)

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)

