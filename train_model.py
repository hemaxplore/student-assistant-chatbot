import json
import pickle
import os
import re
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")
INTENTS_PATH = os.path.join(BASE_DIR, "intents.json")

os.makedirs(MODEL_DIR, exist_ok=True)

# -----------------------------
# Text cleaning (MATCH APP)
# -----------------------------
def clean_text(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    return text

# -----------------------------
# Load intents
# -----------------------------
with open(INTENTS_PATH, "r", encoding="utf-8") as f:
    intents = json.load(f)

texts, labels = [], []

for intent in intents["intents"]:
    for pattern in intent["patterns"]:
        texts.append(clean_text(pattern))
        labels.append(intent["tag"])

# -----------------------------
# Encode labels
# -----------------------------
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(labels)

# -----------------------------
# Vectorization
# -----------------------------
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=7000
)

X = vectorizer.fit_transform(texts)

# -----------------------------
# Train-test split
# -----------------------------
num_classes = len(set(y))
test_size = 0.2
min_test_samples = int(len(y) * test_size)

if min_test_samples < num_classes:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )
else:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

# -----------------------------
# Model
# -----------------------------
base_model = LogisticRegression(
    max_iter=4000,
    class_weight="balanced"
)

class_counts = Counter(y_train)

if min(class_counts.values()) < 3:
    model = base_model
    model.fit(X_train, y_train)
else:
    model = CalibratedClassifierCV(base_model, cv=3)
    model.fit(X_train, y_train)

# -----------------------------
# Save models
# -----------------------------
pickle.dump(model, open(os.path.join(MODEL_DIR, "chatbot_model.pkl"), "wb"))
pickle.dump(vectorizer, open(os.path.join(MODEL_DIR, "vectorizer.pkl"), "wb"))
pickle.dump(label_encoder, open(os.path.join(MODEL_DIR, "label_encoder.pkl"), "wb"))

print("✅ Model trained successfully")
