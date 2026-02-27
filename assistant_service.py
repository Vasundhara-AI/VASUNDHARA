import json
import queue
import threading
from datetime import datetime

from ai_engine import AIEngine
from commands import handle_command
from config import ASSISTANT_GREETING, EXIT_KEYWORDS, LISTEN_SECONDS
from voice import VoiceEngine


class AssistantService:
    def __init__(self):
        self.voice = None
        self.ai = None
        self.ready = False
        self.is_listening = False
        self.speak_enabled = True

        self.events = queue.Queue()
        self.operation_lock = threading.Lock()
        self.stop_listen_event = threading.Event()

    def emit(self, event_type, payload=None):
        message = {
            "event": event_type,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "payload": payload or {},
        }
        self.events.put(message)

    def drain_events(self):
        items = []
        while True:
            try:
                items.append(self.events.get_nowait())
            except queue.Empty:
                return items

    def initialize(self):
        try:
            self.emit("status", {"text": "Loading speech engine..."})
            self.voice = VoiceEngine()
            self.emit("status", {"text": "Loading language model..."})
            self.ai = AIEngine()
            self.ready = True
            self.emit("status", {"text": "Ready"})
            self.emit("assistant_message", {"text": ASSISTANT_GREETING})
            threading.Thread(target=self.voice.speak, args=(ASSISTANT_GREETING,), daemon=True).start()
        except Exception as exc:
            self.emit("status", {"text": "Initialization failed"})
            self.emit("system_message", {"text": f"Startup failed: {exc}"})

    def set_speak_enabled(self, enabled):
        self.speak_enabled = bool(enabled)
        return {"ok": True, "speak_enabled": self.speak_enabled}

    def clear_chat(self):
        self.emit("chat_cleared", {})
        return {"ok": True}

    def _capture_transcript_locked(self):
        self.emit("status", {"text": f"Listening ({LISTEN_SECONDS}s)..."})
        audio_data = self.voice.listen(LISTEN_SECONDS)
        if self.stop_listen_event.is_set():
            return None

        self.emit("status", {"text": "Transcribing..."})
        transcript = self.voice.transcribe(audio_data).strip()
        if not transcript or len(transcript) < 2:
            self.emit("system_message", {"text": "No clear speech detected."})
            return None

        self.emit("user_message", {"text": transcript})
        return transcript

    def _process_transcript_locked(self, transcript):
        lowered = transcript.lower()
        if any(word in lowered for word in EXIT_KEYWORDS):
            response = "Goodbye!"
            self.emit("assistant_message", {"text": response})
            if self.speak_enabled and self.voice is not None:
                self.emit("status", {"text": "Speaking..."})
                self.voice.speak(response)
            self.stop_listen_event.set()
            self.is_listening = False
            self.emit("voice_state", {"is_listening": False})
            return

        self.emit("status", {"text": "Thinking..."})
        response, handled = handle_command(transcript)
        if not handled:
            response = self.ai.generate_response(transcript)

        self.emit("assistant_message", {"text": response})
        if self.speak_enabled and self.voice is not None:
            self.emit("status", {"text": "Speaking..."})
            self.voice.speak(response)

    def send_text(self, text):
        if not self.ready:
            return {"ok": False, "error": "Assistant not ready."}

        text = text.strip()
        if not text:
            return {"ok": False, "error": "Empty text."}

        if not self.operation_lock.acquire(blocking=False):
            self.emit("system_message", {"text": "Assistant is busy. Try again in a moment."})
            return {"ok": False, "error": "Assistant busy."}

        self.emit("user_message", {"text": text})
        try:
            self._process_transcript_locked(text)
        except Exception as exc:
            self.emit("system_message", {"text": f"Processing error: {exc}"})
            return {"ok": False, "error": str(exc)}
        finally:
            self.operation_lock.release()
            if self.ready and not self.is_listening:
                self.emit("status", {"text": "Ready"})

        return {"ok": True}

    def listen_once(self):
        if not self.ready:
            return {"ok": False, "error": "Assistant not ready."}

        def worker():
            if not self.operation_lock.acquire(blocking=False):
                self.emit("system_message", {"text": "Assistant is busy. Try again in a moment."})
                return
            try:
                transcript = self._capture_transcript_locked()
                if transcript:
                    self._process_transcript_locked(transcript)
            except Exception as exc:
                self.emit("system_message", {"text": f"Voice error: {exc}"})
            finally:
                self.operation_lock.release()
                if self.ready and not self.is_listening:
                    self.emit("status", {"text": "Ready"})

        threading.Thread(target=worker, daemon=True).start()
        return {"ok": True}

    def start_voice(self):
        if not self.ready:
            return {"ok": False, "error": "Assistant not ready."}
        if self.is_listening:
            return {"ok": False, "error": "Voice mode already running."}

        self.is_listening = True
        self.stop_listen_event.clear()
        self.emit("system_message", {"text": "Continuous voice mode started."})
        self.emit("voice_state", {"is_listening": True})

        def worker():
            while not self.stop_listen_event.is_set():
                acquired = self.operation_lock.acquire(timeout=0.2)
                if not acquired:
                    continue
                try:
                    transcript = self._capture_transcript_locked()
                    if transcript:
                        self._process_transcript_locked(transcript)
                except Exception as exc:
                    self.emit("system_message", {"text": f"Voice loop error: {exc}"})
                    break
                finally:
                    self.operation_lock.release()

            if self.is_listening:
                self.emit("system_message", {"text": "Continuous voice mode stopped."})
            self.is_listening = False
            self.emit("voice_state", {"is_listening": False})
            if self.ready:
                self.emit("status", {"text": "Ready"})

        threading.Thread(target=worker, daemon=True).start()
        return {"ok": True}

    def stop_voice(self):
        self.stop_listen_event.set()
        return {"ok": True}


def write_json_line(payload):
    print(json.dumps(payload), flush=True)


def main():
    service = AssistantService()
    service.emit("status", {"text": "Initializing..."})
    service.emit("system_message", {"text": "Loading models. First startup can take a while."})
    service.initialize()

    for event in service.drain_events():
        write_json_line(event)

    while True:
        try:
            raw = input()
        except EOFError:
            break

        if not raw.strip():
            continue

        try:
            request = json.loads(raw)
        except json.JSONDecodeError:
            write_json_line({"event": "error", "payload": {"error": "Invalid JSON request"}})
            continue

        action = request.get("action")
        request_id = request.get("request_id")
        payload = request.get("payload") or {}

        if action == "send_text":
            result = service.send_text(payload.get("text", ""))
        elif action == "listen_once":
            result = service.listen_once()
        elif action == "start_voice":
            result = service.start_voice()
        elif action == "stop_voice":
            result = service.stop_voice()
        elif action == "set_speak_enabled":
            result = service.set_speak_enabled(payload.get("enabled", True))
        elif action == "clear_chat":
            result = service.clear_chat()
        elif action == "poll":
            result = {"ok": True}
        else:
            result = {"ok": False, "error": f"Unknown action: {action}"}

        write_json_line(
            {
                "event": "action_result",
                "payload": {"action": action, "request_id": request_id, "result": result},
            }
        )
        for event in service.drain_events():
            write_json_line(event)


if __name__ == "__main__":
    main()
