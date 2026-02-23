p = r"d:\VHACK\VHACK_2.0\assistant.py"
lt = chr(60)   # <
gt = chr(62)   # >
pipe = chr(124) # |

code = f"""import os, re, subprocess, webbrowser, datetime, glob
import numpy as np
import sounddevice as sd
import whisper
import pyttsx3
from llama_cpp import Llama

LLM_MODEL_PATH = "models/phi-3-mini-4k-instruct.gguf"
STT_MODEL_NAME = "base.en"
SAMPLE_RATE = 16000
CHANNELS = 1
USERNAME = os.environ.get("USERNAME", "")

APP_MAP = {{
    "whatsapp":      rf"C:\\\\Users\\\\{{USERNAME}}\\\\AppData\\\\Local\\\\WhatsApp\\\\WhatsApp.exe",
    "telegram":      rf"C:\\\\Users\\\\{{USERNAME}}\\\\AppData\\\\Roaming\\\\Telegram Desktop\\\\Telegram.exe",
    "discord":       rf"C:\\\\Users\\\\{{USERNAME}}\\\\AppData\\\\Local\\\\Discord\\\\app-*\\\\Discord.exe",
    "chrome":        r"C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe",
    "firefox":       r"C:\\\\Program Files\\\\Mozilla Firefox\\\\firefox.exe",
    "edge":          r"C:\\\\Program Files (x86)\\\\Microsoft\\\\Edge\\\\Application\\\\msedge.exe",
    "word":          r"C:\\\\Program Files\\\\Microsoft Office\\\\root\\\\Office16\\\\WINWORD.EXE",
    "excel":         r"C:\\\\Program Files\\\\Microsoft Office\\\\root\\\\Office16\\\\EXCEL.EXE",
    "powerpoint":    r"C:\\\\Program Files\\\\Microsoft Office\\\\root\\\\Office16\\\\POWERPNT.EXE",
    "notepad":       "notepad.exe",
    "calculator":    "calc.exe",
    "paint":         "mspaint.exe",
    "file explorer": "explorer.exe",
    "task manager":  "taskmgr.exe",
    "camera":        "microsoft.windows.camera:",
    "settings":      "ms-settings:",
    "vs code":       rf"C:\\\\Users\\\\{{USERNAME}}\\\\AppData\\\\Local\\\\Programs\\\\Microsoft VS Code\\\\Code.exe",
    "vscode":        rf"C:\\\\Users\\\\{{USERNAME}}\\\\AppData\\\\Local\\\\Programs\\\\Microsoft VS Code\\\\Code.exe",
    "terminal":      "wt.exe",
    "cmd":           "cmd.exe",
    "powershell":    "powershell.exe",
    "spotify":       rf"C:\\\\Users\\\\{{USERNAME}}\\\\AppData\\\\Roaming\\\\Spotify\\\\Spotify.exe",
    "vlc":           r"C:\\\\Program Files\\\\VideoLAN\\\\VLC\\\\vlc.exe",
}}

WEBSITE_MAP = {{
    "youtube":   "https://www.youtube.com",
    "google":    "https://www.google.com",
    "gmail":     "https://mail.google.com",
    "github":    "https://www.github.com",
    "netflix":   "https://www.netflix.com",
    "twitter":   "https://www.twitter.com",
    "instagram": "https://www.instagram.com",
    "facebook":  "https://www.facebook.com",
    "reddit":    "https://www.reddit.com",
    "linkedin":  "https://www.linkedin.com",
    "amazon":    "https://www.amazon.in",
    "maps":      "https://maps.google.com",
    "chatgpt":   "https://chat.openai.com",
}}

def resolve_app_path(raw_path):
    if "*" in raw_path:
        matches = glob.glob(raw_path)
        return matches[-1] if matches else raw_path
    return raw_path

def launch_app(name):
    path = resolve_app_path(APP_MAP[name])
    if ":" in path and not os.path.splitext(path)[1]:
        try:
            os.startfile(path)
            return f"Opening {{name}}."
        except Exception:
            return f"Sorry, I could not open {{name}}."
    if os.path.exists(path):
        subprocess.Popen([path])
        return f"Opening {{name}}."
    try:
        subprocess.Popen(path, shell=True)
        return f"Opening {{name}}."
    except Exception:
        return f"Sorry, I could not find {{name}} on your system."

def handle_command(transcript):
    text = transcript.lower().strip()
    open_match = re.search(r"\\\\b(?:open|launch|start|run)\\\\b\\\\s+(.+)", text)
    if open_match:
        target = open_match.group(1).strip().rstrip(".")
        for app_name in APP_MAP:
            if app_name in target:
                return launch_app(app_name), True
        for site_name, url in WEBSITE_MAP.items():
            if site_name in target:
                webbrowser.open(url)
                return f"Opening {{site_name}} in your browser.", True
    search_match = re.search(r"\\\\b(?:search|google|look up|find)\\\\b\\\\s+(?:for\\\\s+)?(.+)", text)
    if search_match:
        query = search_match.group(1).strip().rstrip(".")
        webbrowser.open("https://www.google.com/search?q=" + query.replace(" ", "+"))
        return f"Searching Google for {{query}}.", True
    yt_match = re.search(r"\\\\bplay\\\\b\\\\s+(.+?)\\\\s+(?:on\\\\s+)?(?:youtube|yt)\\\\b", text)
    if yt_match:
        query = yt_match.group(1).strip()
        webbrowser.open("https://www.youtube.com/results?search_query=" + query.replace(" ", "+"))
        return f"Playing {{query}} on YouTube.", True
    if re.search(r"\\\\b(?:what(?:s| is)(?: the)? (?:time|date|day)|current time|todays date)\\\\b", text):
        now = datetime.datetime.now()
        return f"It is {{now.strftime(\x27%I:%M %p\x27)}} on {{now.strftime(\x27%A, %B %d, %Y\x27)}}.", True
    if re.search(r"\\\\b(?:mute|unmute)\\\\b", text):
        subprocess.Popen(["powershell", "-Command", "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait([char]173)"])
        action = "muted" if "mute" in text and "unmute" not in text else "unmuted"
        return f"Audio {{action}}.", True
    if re.search(r"\\\\b(?:volume up|increase volume|louder)\\\\b", text):
        for _ in range(5): subprocess.Popen(["powershell","-Command","Add-Type -AssemblyName System.Windows.Forms;[System.Windows.Forms.SendKeys]::SendWait([char]175)"])
        return "Volume increased.", True
    if re.search(r"\\\\b(?:volume down|decrease volume|quieter|lower volume)\\\\b", text):
        for _ in range(5): subprocess.Popen(["powershell","-Command","Add-Type -AssemblyName System.Windows.Forms;[System.Windows.Forms.SendKeys]::SendWait([char]174)"])
        return "Volume decreased.", True
    if re.search(r"\\\\bcancel shutdown\\\\b", text):
        subprocess.Popen(["shutdown", "/a"])
        return "Shutdown cancelled.", True
    if re.search(r"\\\\b(?:shut ?down|power off)\\\\b", text):
        subprocess.Popen(["shutdown", "/s", "/t", "10"])
        return "Shutting down in 10 seconds.", True
    if re.search(r"\\\\brestart\\\\b", text):
        subprocess.Popen(["shutdown", "/r", "/t", "10"])
        return "Restarting in 10 seconds.", True
    if re.search(r"\\\\bsleep\\\\b", text):
        subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
        return "Putting your computer to sleep.", True
    return None, False

class VoiceAssistant:
    def __init__(self):
        print("Initializing Voice Assistant...")
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty("rate", 150)
        print(f"Loading Whisper model: {{STT_MODEL_NAME}}...")
        self.stt_model = whisper.load_model(STT_MODEL_NAME)
        print(f"Loading LLM model: {{LLM_MODEL_PATH}}...")
        self.llm = Llama(model_path=LLM_MODEL_PATH, n_ctx=2048, verbose=False)

    def speak(self, text):
        print(f"Assistant: {{text}}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def listen(self, duration=5):
        print(f"\\nListening for {{duration}} seconds...")
        recording = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16")
        sd.wait()
        print("Processing audio...")
        return recording.flatten().astype(np.float32) / 32768.0

    def transcribe(self, audio_data):
        result = self.stt_model.transcribe(audio_data, fp16=False)
        return result["text"].strip()

    def generate_response(self, text):
        u_tag = "{lt}{pipe}user{pipe}{gt}"
        e_tag = "{lt}{pipe}end{pipe}{gt}"
        a_tag = "{lt}{pipe}assistant{pipe}{gt}"
        prompt = f"{{u_tag}}\\n{{text}}{{e_tag}}\\n{{a_tag}}"
        output = self.llm(prompt, max_tokens=256, stop=[e_tag], echo=False)
        return output["choices"][0]["text"].strip()

    def run(self):
        self.speak("Hello! I am your voice assistant. How can I help you?")
        while True:
            try:
                audio_data = self.listen()
                transcript = self.transcribe(audio_data)
                if not transcript or len(transcript) < 2:
                    print("No clear speech detected.")
                    continue
                print(f"You: {{transcript}}")
                if any(w in transcript.lower() for w in ["exit", "stop", "goodbye", "bye"]):
                    self.speak("Goodbye!")
                    break
                response, handled = handle_command(transcript)
                if not handled:
                    response = self.generate_response(transcript)
                self.speak(response)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {{e}}")
                continue

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
"""

with open(p, "w", encoding="utf-8") as f:
    f.write(code)
print("Written successfully!")

