import datetime
import glob
import os
import re
import subprocess
import webbrowser

from config import APP_MAP, WEBSITE_MAP


def resolve_app_path(raw_path):
    if "*" in raw_path:
        matches = glob.glob(raw_path)
        return matches[-1] if matches else raw_path
    return raw_path


def launch_app(name):
    path = resolve_app_path(APP_MAP[name])

    if path.startswith("shell:"):
        try:
            subprocess.Popen(["explorer", path])
            return f"Opening {name}."
        except Exception:
            return f"Sorry, I could not open {name}."

    if ":" in path and not os.path.splitext(path)[1]:
        try:
            os.startfile(path)
            return f"Opening {name}."
        except Exception:
            return f"Sorry, I could not open {name}."

    if os.path.exists(path):
        subprocess.Popen([path])
        return f"Opening {name}."

    try:
        subprocess.Popen(path, shell=True)
        return f"Opening {name}."
    except Exception:
        return f"Sorry, I could not find {name} on your system."


def _send_media_key(key_code):
    command = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        f"[System.Windows.Forms.SendKeys]::SendWait([char]{key_code})"
    )
    subprocess.Popen(["powershell", "-Command", command])


def handle_command(transcript):
    text = transcript.lower().strip()

    open_match = re.search(r"\b(?:open|launch|start|run)\b\s+(.+)", text)
    if open_match:
        target = open_match.group(1).strip().rstrip(".")
        for app_name in APP_MAP:
            if app_name in target:
                return launch_app(app_name), True
        for site_name, url in WEBSITE_MAP.items():
            if site_name in target:
                webbrowser.open(url)
                return f"Opening {site_name} in your browser.", True

    search_match = re.search(r"\b(?:search|google|look up|find)\b\s+(?:for\s+)?(.+)", text)
    if search_match:
        query = search_match.group(1).strip().rstrip(".")
        webbrowser.open("https://www.google.com/search?q=" + query.replace(" ", "+"))
        return f"Searching Google for {query}.", True

    yt_match = re.search(r"\bplay\b\s+(.+?)\s+(?:on\s+)?(?:youtube|yt)\b", text)
    if yt_match:
        query = yt_match.group(1).strip()
        webbrowser.open("https://www.youtube.com/results?search_query=" + query.replace(" ", "+"))
        return f"Playing {query} on YouTube.", True

    if re.search(r"\b(?:what(?:'s| is)(?: the)? (?:time|date|day)|current time|today(?:'s)? date)\b", text):
        now = datetime.datetime.now()
        return f"It is {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}.", True

    if re.search(r"\b(?:mute|unmute)\b", text):
        _send_media_key(173)
        action = "muted" if "mute" in text and "unmute" not in text else "unmuted"
        return f"Audio {action}.", True

    if re.search(r"\b(?:volume up|increase volume|louder)\b", text):
        for _ in range(5):
            _send_media_key(175)
        return "Volume increased.", True

    if re.search(r"\b(?:volume down|decrease volume|quieter|lower volume)\b", text):
        for _ in range(5):
            _send_media_key(174)
        return "Volume decreased.", True

    if re.search(r"\bcancel shutdown\b", text):
        subprocess.Popen(["shutdown", "/a"])
        return "Shutdown cancelled.", True

    if re.search(r"\b(?:shut ?down|power off)\b", text):
        subprocess.Popen(["shutdown", "/s", "/t", "10"])
        return "Shutting down in 10 seconds.", True

    if re.search(r"\brestart\b", text):
        subprocess.Popen(["shutdown", "/r", "/t", "10"])
        return "Restarting in 10 seconds.", True

    if re.search(r"\bsleep\b", text):
        subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
        return "Putting your computer to sleep.", True

    return None, False
