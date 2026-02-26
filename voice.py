import numpy as np
import pyttsx3
import sounddevice as sd
import whisper

from config import CHANNELS, SAMPLE_RATE, STT_MODEL_NAME


class VoiceEngine:
    def __init__(self):
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty("rate", 150)
        print(f"Loading Whisper model: {STT_MODEL_NAME}...")
        self.stt_model = whisper.load_model(STT_MODEL_NAME)

    def speak(self, text):
        print(f"Assistant: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def listen(self, duration):
        print(f"\nListening for {duration} seconds...")
        recording = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
        )
        sd.wait()
        print("Processing audio...")
        return recording.flatten().astype(np.float32) / 32768.0

    def transcribe(self, audio_data):
        result = self.stt_model.transcribe(audio_data, fp16=False)
        return result["text"].strip()
