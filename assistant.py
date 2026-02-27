import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext, ttk

from ai_engine import AIEngine
from commands import handle_command
from config import ASSISTANT_GREETING, EXIT_KEYWORDS, LISTEN_SECONDS
from voice import VoiceEngine


class AssistantGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Windows AI Assistant")
        self.root.geometry("980x680")
        self.root.minsize(880, 560)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.voice = None
        self.ai = None
        self.ready = False
        self.is_listening = False
        self.speak_enabled = True

        self.ui_queue = queue.Queue()
        self.operation_lock = threading.Lock()
        self.stop_listen_event = threading.Event()

        self.status_var = tk.StringVar(value="Initializing...")
        self.speak_var = tk.BooleanVar(value=True)
        self.input_var = tk.StringVar()

        self._build_ui()
        self._set_controls_enabled(False)
        self._append_system("Loading models. First startup can take a while.")

        self.speak_var.trace_add("write", self._on_speak_toggle)
        threading.Thread(target=self._initialize_engines, daemon=True).start()
        self.root.after(100, self._drain_ui_queue)

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(container)
        header.pack(fill=tk.X, pady=(0, 10))

        title = ttk.Label(
            header,
            text="Windows AI Assistant",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(side=tk.LEFT)

        status = ttk.Label(
            header,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
        )
        status.pack(side=tk.RIGHT)

        self.chat_box = scrolledtext.ScrolledText(
            container,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            state=tk.DISABLED,
            height=24,
        )
        self.chat_box.pack(fill=tk.BOTH, expand=True)
        self.chat_box.tag_configure("you", foreground="#2563eb")
        self.chat_box.tag_configure("assistant", foreground="#059669")
        self.chat_box.tag_configure("system", foreground="#7c3aed")
        self.chat_box.tag_configure("time", foreground="#6b7280")

        controls = ttk.Frame(container)
        controls.pack(fill=tk.X, pady=(10, 0))

        entry = ttk.Entry(controls, textvariable=self.input_var, font=("Segoe UI", 11))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        entry.bind("<Return>", self._on_send)
        self.input_entry = entry

        self.send_button = ttk.Button(controls, text="Send", command=self._on_send)
        self.send_button.pack(side=tk.LEFT, padx=(0, 8))

        self.listen_once_button = ttk.Button(controls, text="Listen Once", command=self._listen_once)
        self.listen_once_button.pack(side=tk.LEFT, padx=(0, 8))

        self.start_voice_button = ttk.Button(controls, text="Start Voice", command=self._start_voice_loop)
        self.start_voice_button.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_voice_button = ttk.Button(controls, text="Stop Voice", command=self._stop_voice_loop)
        self.stop_voice_button.pack(side=tk.LEFT, padx=(0, 8))

        options = ttk.Frame(container)
        options.pack(fill=tk.X, pady=(10, 0))

        self.speak_checkbox = ttk.Checkbutton(
            options,
            text="Speak assistant responses",
            variable=self.speak_var,
        )
        self.speak_checkbox.pack(side=tk.LEFT)

        self.clear_button = ttk.Button(options, text="Clear Chat", command=self._clear_chat)
        self.clear_button.pack(side=tk.RIGHT)

    def _queue_ui(self, callback, *args):
        self.ui_queue.put((callback, args))

    def _drain_ui_queue(self):
        while True:
            try:
                callback, args = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            callback(*args)
        self.root.after(100, self._drain_ui_queue)

    def _set_status(self, text):
        self.status_var.set(text)

    def _set_status_async(self, text):
        self._queue_ui(self._set_status, text)

    def _set_controls_enabled(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        for widget in (
            self.input_entry,
            self.send_button,
            self.listen_once_button,
            self.start_voice_button,
            self.stop_voice_button,
            self.speak_checkbox,
            self.clear_button,
        ):
            widget.configure(state=state)
        if enabled and not self.is_listening:
            self.stop_voice_button.configure(state=tk.DISABLED)

    def _append_message(self, role, text, tag):
        now = datetime.now().strftime("%H:%M:%S")
        self.chat_box.configure(state=tk.NORMAL)
        self.chat_box.insert(tk.END, f"[{now}] ", ("time",))
        self.chat_box.insert(tk.END, f"{role}: ", (tag,))
        self.chat_box.insert(tk.END, f"{text}\n")
        self.chat_box.configure(state=tk.DISABLED)
        self.chat_box.see(tk.END)

    def _append_user(self, text):
        self._append_message("You", text, "you")

    def _append_assistant(self, text):
        self._append_message("Assistant", text, "assistant")

    def _append_system(self, text):
        self._append_message("System", text, "system")

    def _clear_chat(self):
        self.chat_box.configure(state=tk.NORMAL)
        self.chat_box.delete("1.0", tk.END)
        self.chat_box.configure(state=tk.DISABLED)

    def _on_speak_toggle(self, *_):
        self.speak_enabled = bool(self.speak_var.get())

    def _initialize_engines(self):
        try:
            self._set_status_async("Loading speech engine...")
            voice = VoiceEngine()
            self._set_status_async("Loading language model...")
            ai = AIEngine()

            self._queue_ui(self._on_ready, voice, ai)
        except Exception as exc:
            self._queue_ui(self._on_init_error, str(exc))

    def _on_ready(self, voice, ai):
        self.voice = voice
        self.ai = ai
        self.ready = True
        self._set_controls_enabled(True)
        self._set_status("Ready")
        self._append_assistant(ASSISTANT_GREETING)

        threading.Thread(target=self.voice.speak, args=(ASSISTANT_GREETING,), daemon=True).start()

    def _on_init_error(self, error_text):
        self._set_status("Initialization failed")
        self._append_system(f"Startup failed: {error_text}")
        messagebox.showerror("Initialization Error", error_text)

    def _run_text_query(self, text):
        if not self.ready:
            return

        acquired = self.operation_lock.acquire(blocking=False)
        if not acquired:
            self._queue_ui(self._append_system, "Assistant is busy. Try again in a moment.")
            return

        try:
            self._process_transcript_locked(text)
        finally:
            self.operation_lock.release()
            if self.ready and not self.is_listening:
                self._set_status_async("Ready")

    def _process_transcript_locked(self, transcript):
        lowered = transcript.lower()
        if any(word in lowered for word in EXIT_KEYWORDS):
            response = "Goodbye!"
            self._queue_ui(self._append_assistant, response)
            if self.speak_enabled and self.voice is not None:
                self._set_status_async("Speaking...")
                self.voice.speak(response)
            self.stop_listen_event.set()
            self._queue_ui(self._stop_voice_ui)
            return

        self._set_status_async("Thinking...")
        response, handled = handle_command(transcript)
        if not handled:
            response = self.ai.generate_response(transcript)

        self._queue_ui(self._append_assistant, response)
        if self.speak_enabled and self.voice is not None:
            self._set_status_async("Speaking...")
            self.voice.speak(response)

    def _capture_transcript_locked(self):
        self._set_status_async(f"Listening ({LISTEN_SECONDS}s)...")
        audio_data = self.voice.listen(LISTEN_SECONDS)
        if self.stop_listen_event.is_set():
            return None

        self._set_status_async("Transcribing...")
        transcript = self.voice.transcribe(audio_data).strip()
        if not transcript or len(transcript) < 2:
            self._queue_ui(self._append_system, "No clear speech detected.")
            return None

        self._queue_ui(self._append_user, transcript)
        return transcript

    def _listen_once_worker(self):
        acquired = self.operation_lock.acquire(blocking=False)
        if not acquired:
            self._queue_ui(self._append_system, "Assistant is busy. Try again in a moment.")
            return

        try:
            transcript = self._capture_transcript_locked()
            if transcript:
                self._process_transcript_locked(transcript)
        except Exception as exc:
            self._queue_ui(self._append_system, f"Voice error: {exc}")
        finally:
            self.operation_lock.release()
            if self.ready and not self.is_listening:
                self._set_status_async("Ready")

    def _voice_loop_worker(self):
        while not self.stop_listen_event.is_set():
            acquired = self.operation_lock.acquire(timeout=0.2)
            if not acquired:
                continue

            try:
                transcript = self._capture_transcript_locked()
                if transcript:
                    self._process_transcript_locked(transcript)
            except Exception as exc:
                self._queue_ui(self._append_system, f"Voice loop error: {exc}")
                break
            finally:
                self.operation_lock.release()

        self._queue_ui(self._stop_voice_ui)
        if self.ready:
            self._set_status_async("Ready")

    def _on_send(self, _event=None):
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set("")
        self._append_user(text)
        threading.Thread(target=self._run_text_query, args=(text,), daemon=True).start()

    def _listen_once(self):
        if not self.ready:
            return
        threading.Thread(target=self._listen_once_worker, daemon=True).start()

    def _start_voice_loop(self):
        if not self.ready or self.is_listening:
            return
        self.is_listening = True
        self.stop_listen_event.clear()
        self._append_system("Continuous voice mode started.")
        self.start_voice_button.configure(state=tk.DISABLED)
        self.stop_voice_button.configure(state=tk.NORMAL)
        threading.Thread(target=self._voice_loop_worker, daemon=True).start()

    def _stop_voice_ui(self):
        if self.is_listening:
            self._append_system("Continuous voice mode stopped.")
        self.is_listening = False
        self.start_voice_button.configure(state=tk.NORMAL if self.ready else tk.DISABLED)
        self.stop_voice_button.configure(state=tk.DISABLED)

    def _stop_voice_loop(self):
        self.stop_listen_event.set()
        self._stop_voice_ui()

    def _on_close(self):
        self.stop_listen_event.set()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AssistantGUI()
    app.run()
