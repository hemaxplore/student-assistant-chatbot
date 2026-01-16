from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import random, time
from datetime import datetime

# -----------------------------
# Try importing DB + ML safely
# -----------------------------
try:
    import mysql.connector
    DB_AVAILABLE = True
except Exception as e:
    print("DB module not available:", e)
    DB_AVAILABLE = False

try:
    from chatbot_core import predict_intent, get_response
except Exception as e:
    print("ML model not available:", e)
    def predict_intent(text): return "default", 0.0
    def get_response(intent_tag): return "Hmm 🤔 I’m not sure. Can you rephrase?"
    
app = Flask(__name__)
app.secret_key = "student_assistant_secret_key"

# -----------------------------
# Session config
# -----------------------------
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)

# -----------------------------
# MySQL config
# -----------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "student_assistant"
}

def get_db_safe():
    if not DB_AVAILABLE:
        return None
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print("DB skipped:", e)
        return None

# -----------------------------
# Save message (DB optional)
# -----------------------------
def save_message(username, sender, message):
    now = datetime.now()
    conn = get_db_safe()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO chat_history (username, sender, message, timestamp) VALUES (%s,%s,%s,%s)",
                (username, sender, message, now)
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("DB save skipped:", e)
    if "history" not in session:
        session["history"] = []
    session["history"].append({
        "sender": sender,
        "message": message,
        "time": now.strftime("%I:%M %p"),
        "date": now.strftime("%Y-%m-%d")
    })

# -----------------------------
# Load history (DB optional)
# -----------------------------
def load_messages(username):
    conn = get_db_safe()
    if not conn:
        return session.get("history", [])
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

# -----------------------------
# Login
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        conn = get_db_safe()
        user = None
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE email=%s AND password=%s", (email, password))
            user = cur.fetchone()
            cur.close()
            conn.close()
        if user or conn is None:
            session.clear()
            session["user"] = email
            session["last_intent"] = None
            session["history"] = []
            return redirect(url_for("chat_page"))
        return render_template("login.html", error="❌ Invalid login")
    return render_template("login.html")

# -----------------------------
# Chat page
# -----------------------------
@app.route("/chatbot")
def chat_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", user=session["user"])

# -----------------------------
# Load chat history
# -----------------------------
@app.route("/load_history")
def load_history():
    if "user" not in session:
        return jsonify({"history": []})
    username = session["user"]
    session_history = session.get("history", [])
    if session_history:
        return jsonify({"history": session_history})
    db_history = load_messages(username)
    session["history"] = db_history
    return jsonify({"history": db_history})

# -----------------------------
# Chat API
# -----------------------------
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
    import time, random
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

# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app.run()
