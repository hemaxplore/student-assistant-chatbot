# chatbot_core.py

import json
import os
import pickle
import re
import numpy as np

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")
INTENTS_PATH = os.path.join(BASE_DIR, "intents.json")

MODEL_PATH = os.path.join(MODEL_DIR, "chatbot_model.pkl")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")

# -----------------------------
# Load intents
# -----------------------------
with open(INTENTS_PATH, "r", encoding="utf-8") as f:
    intents = json.load(f)

# -----------------------------
# Load trained components
# -----------------------------
try:
    model = pickle.load(open(MODEL_PATH, "rb"))
    vectorizer = pickle.load(open(VECTORIZER_PATH, "rb"))
    label_encoder = pickle.load(open(ENCODER_PATH, "rb"))
    MODEL_READY = True
    print("✅ chatbot_core: Model loaded successfully")
except Exception as e:
    MODEL_READY = False
    print("❌ chatbot_core: Model loading failed:", e)

# -----------------------------
# Hard rule overrides (CRITICAL)
# -----------------------------
HARD_RULES = {
    # greetings
    "hi": "greeting",
    "hello": "greeting",
    "hey": "greeting",
    "hai": "greeting",
    "hii": "greeting",
    "helo": "greeting",
    "good morning": "greeting",
    "good afternoon": "greeting",
    "good evening": "greeting",

    # goodbye
    "bye": "goodbye",
    "bye bye": "goodbye",
    "goodbye": "goodbye",
    "exit": "goodbye",
    "quit": "goodbye",
    "end chat": "goodbye",
    "ok bye": "goodbye",
    "i am leaving": "goodbye",
    "i am done": "goodbye",

    # thanks
    "thanks": "thanks",
    "thank you": "thanks",
    "thanks a lot": "thanks",
    "thank you so much": "thanks",
    "appreciate it": "thanks",
    "thanks for help": "thanks",
    "many thanks": "thanks"
}

# -----------------------------
# Text cleaning (MUST match training)
# -----------------------------
def clean_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

# -----------------------------
# Predict intent + confidence
# -----------------------------
def predict_intent(text: str):
    """
    Returns:
        intent (str)
        confidence (float 0.0–1.0)
    """

    if not MODEL_READY:
        return "default", 0.0

    cleaned_text = clean_text(text)

    # ✅ STEP 1: Rule-based override (fixes short-text confusion)
    if cleaned_text in HARD_RULES:
        return HARD_RULES[cleaned_text], 0.99

    # ✅ STEP 2: ML-based prediction
    X = vectorizer.transform([cleaned_text])
    probs = model.predict_proba(X)[0]

    max_index = np.argmax(probs)
    confidence = float(probs[max_index])
    intent = label_encoder.inverse_transform([max_index])[0]

    return intent, confidence

# -----------------------------
# Get response
# -----------------------------
def get_response(intent_tag: str) -> str:
    for intent in intents["intents"]:
        if intent["tag"] == intent_tag:
            return np.random.choice(intent["responses"])

    # Fallback to default
    for intent in intents["intents"]:
        if intent["tag"] == "default":
            return np.random.choice(intent["responses"])

    return "Sorry, I didn’t understand that."
