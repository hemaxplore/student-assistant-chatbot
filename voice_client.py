import speech_recognition as sr
import pyttsx3
import requests
import keyboard
import time

API_URL = "http://127.0.0.1:5000/chat"

engine = pyttsx3.init()
engine.setProperty("rate", 160)

recognizer = sr.Recognizer()
recognizer.pause_threshold = 0.8

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    with sr.Microphone() as source:
        print("🎤 Listening...")
        audio = recognizer.listen(source, timeout=6, phrase_time_limit=6)
        return recognizer.recognize_google(audio, language="en-IN")

def main():
    speak("Press space to talk.")
    while True:
        keyboard.wait("space")
        try:
            user_text = listen()
            print("You:", user_text)

            res = requests.post(API_URL, json={"message": user_text}).json()
            bot_reply = res["response"]

            print("Bot:", bot_reply)
            speak(bot_reply)

        except Exception as e:
            print("Error:", e)
            speak("Sorry, I didn't catch that.")

        time.sleep(0.3)

if __name__ == "__main__":
    main()
