import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

PROJECT_ROOT = Path(__file__).resolve().parent
APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else PROJECT_ROOT

if load_dotenv is not None:
    env_candidates = [
        APP_ROOT / ".env",
        APP_ROOT.parent / ".env",
        APP_ROOT.parent.parent / ".env",
        PROJECT_ROOT / ".env",
    ]
    for env_path in env_candidates:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
            break

_raw_llm_model_path = os.getenv("LLM_MODEL_PATH", "models/phi-3-mini-4k-instruct.gguf")
_candidate_llm_path = Path(_raw_llm_model_path).expanduser()
if not _candidate_llm_path.is_absolute():
    _candidate_llm_path = (APP_ROOT / _candidate_llm_path).resolve()

if _candidate_llm_path.exists():
    LLM_MODEL_PATH = str(_candidate_llm_path)
else:
    model_dirs = [
        APP_ROOT / "models",
        APP_ROOT.parent / "models",
        APP_ROOT.parent.parent / "models",
        PROJECT_ROOT / "models",
    ]
    gguf_candidates = []
    for model_dir in model_dirs:
        gguf_candidates.extend(sorted(model_dir.glob("*.gguf")))
    LLM_MODEL_PATH = str(gguf_candidates[0]) if gguf_candidates else str(_candidate_llm_path)

STT_MODEL_NAME = os.getenv("STT_MODEL_NAME", "base.en")
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
CHANNELS = int(os.getenv("CHANNELS", "1"))
LISTEN_SECONDS = float(os.getenv("LISTEN_SECONDS", "3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "128"))
ASSISTANT_GREETING = os.getenv("ASSISTANT_GREETING", "Hello I am Vasundhara")
WAKE_WORDS = (
    "hey vasundhara",
    "hey vasu",
    "ok vasundhara",
    "okay vasu",
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USERNAME = os.environ.get("USERNAME", "")

APP_MAP = {
    "whatsapp": r"shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!WhatsApp",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "camera": "microsoft.windows.camera:",
    "settings": "ms-settings:",
    "vs code": rf"C:\Users\{USERNAME}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "terminal": "wt.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
}

WEBSITE_MAP = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://www.github.com",
    "netflix": "https://www.netflix.com",
    "twitter": "https://www.twitter.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "reddit": "https://www.reddit.com",
    "linkedin": "https://www.linkedin.com",
    "amazon": "https://www.amazon.in",
    "maps": "https://maps.google.com",
    "chat gpt": "https://chat.openai.com",
    "chatgpt": "https://chat.openai.com",
}

EXIT_KEYWORDS = ("exit", "stop", "goodbye", "bye")
