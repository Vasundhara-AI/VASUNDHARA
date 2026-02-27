import os
import queue
import threading

import numpy as np
import pyttsx3
import sounddevice as sd

from config import CHANNELS, SAMPLE_RATE, STT_MODEL_NAME

os.environ.setdefault("NUMBA_THREADING_LAYER", "workqueue")
import whisper


class VoiceEngine:
    def __init__(self):
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty("rate", 150)
        self._tts_queue = queue.Queue()
        self._tts_worker = threading.Thread(target=self._speak_worker, daemon=True)
        self._tts_worker.start()
        print(f"Loading Whisper model: {STT_MODEL_NAME}...")
        self.stt_model = whisper.load_model(STT_MODEL_NAME)

    def _speak_worker(self):
        while True:
            item = self._tts_queue.get()
            if item is None:
                self._tts_queue.task_done()
                return

            text, done_event = item
            try:
                print(f"Assistant: {text}")
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            finally:
                if done_event is not None:
                    done_event.set()
                self._tts_queue.task_done()

    def speak(self, text, wait=True):
        if not text:
            return

        done_event = threading.Event() if wait else None
        self._tts_queue.put((text, done_event))

        if done_event is not None:
            done_event.wait()

    def close(self):
        self._tts_queue.put(None)
        self._tts_worker.join(timeout=1.5)

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
