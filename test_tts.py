import pyttsx3
print("Initializing TTS...")
try:
    engine = pyttsx3.init()
    print("TTS initialized.")
    engine.setProperty('rate', 150)
    print("Speaking test message...")
    engine.say("Hello, this is a test of the text to speech engine.")
    engine.runAndWait()
    print("Test message spoken successfully!")
except Exception as e:
    print(f"Error in TTS: {e}")
