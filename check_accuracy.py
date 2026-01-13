import json
from chatbot_core import predict_intent

# Load intents
with open("intents.json", "r", encoding="utf-8") as f:
    intents = json.load(f)

total = 0
correct = 0
wrong_cases = []

for intent in intents["intents"]:
    tag = intent["tag"]

    for pattern in intent["patterns"]:
        total += 1
        predicted_intent, confidence = predict_intent(pattern)

        if predicted_intent == tag:
            correct += 1
        else:
            wrong_cases.append({
                "text": pattern,
                "expected": tag,
                "predicted": predicted_intent,
                "confidence": round(confidence, 2)
            })

accuracy = (correct / total) * 100

print("\n📊 CHATBOT ACCURACY REPORT")
print("=" * 35)
print(f"Total test samples : {total}")
print(f"Correct predictions: {correct}")
print(f"Wrong predictions  : {total - correct}")
print(f"🎯 Accuracy        : {accuracy:.2f}%")

# Show wrong predictions (important!)
if wrong_cases:
    print("\n❌ WRONG PREDICTIONS (Top 10)")
    print("-" * 35)
    for case in wrong_cases[:10]:
        print(case)
