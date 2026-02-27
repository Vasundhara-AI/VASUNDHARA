const overlay = document.getElementById("overlay");
const orbBtn = document.getElementById("orbBtn");
const closeBtn = document.getElementById("closeBtn");
const chatBox = document.getElementById("chatBox");
const statusPill = document.getElementById("statusPill");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const listenOnceBtn = document.getElementById("listenOnceBtn");
const startVoiceBtn = document.getElementById("startVoiceBtn");
const stopVoiceBtn = document.getElementById("stopVoiceBtn");
const speakEnabled = document.getElementById("speakEnabled");
const clearBtn = document.getElementById("clearBtn");

let isReady = false;
let overlayMode = "compact";

async function setOverlayMode(mode) {
  overlayMode = mode;
  overlay.classList.toggle("expanded", mode === "expanded");
  overlay.classList.toggle("compact", mode !== "expanded");
  await window.assistantApi.setOverlayMode(mode);
  if (mode === "expanded") {
    setTimeout(() => userInput.focus(), 50);
  }
}

function setControlsEnabled(enabled) {
  userInput.disabled = !enabled;
  sendBtn.disabled = !enabled;
  listenOnceBtn.disabled = !enabled;
  startVoiceBtn.disabled = !enabled;
  speakEnabled.disabled = !enabled;
  clearBtn.disabled = !enabled;
  if (!enabled) {
    stopVoiceBtn.disabled = true;
  }
}

function appendMessage(role, text, timestamp = "") {
  const row = document.createElement("article");
  row.className = "chat-row";

  const meta = document.createElement("div");
  meta.className = "chat-meta";

  const roleSpan = document.createElement("span");
  roleSpan.className = `chat-role ${role}`;
  roleSpan.textContent = role === "you" ? "You" : role === "assistant" ? "Assistant" : "System";

  const timeSpan = document.createElement("span");
  timeSpan.className = "chat-time";
  timeSpan.textContent = timestamp ? `[${timestamp}]` : "";

  const content = document.createElement("p");
  content.className = "chat-text";
  content.textContent = text;

  meta.append(roleSpan, timeSpan);
  row.append(meta, content);
  chatBox.appendChild(row);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function setStatus(text) {
  statusPill.textContent = text;
}

async function callAction(action, payload = {}) {
  const result = await window.assistantApi.sendAction(action, payload);
  if (result && result.ok === false && result.error) {
    appendMessage("system", result.error);
  }
}

sendBtn.addEventListener("click", async () => {
  const text = userInput.value.trim();
  if (!text || !isReady) {
    return;
  }
  userInput.value = "";
  await callAction("send_text", { text });
});

userInput.addEventListener("keydown", async (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    sendBtn.click();
  }
});

listenOnceBtn.addEventListener("click", async () => {
  if (!isReady) {
    return;
  }
  await callAction("listen_once");
});

startVoiceBtn.addEventListener("click", async () => {
  if (!isReady) {
    return;
  }
  await callAction("start_voice");
});

stopVoiceBtn.addEventListener("click", async () => {
  await callAction("stop_voice");
});

speakEnabled.addEventListener("change", async () => {
  await callAction("set_speak_enabled", { enabled: speakEnabled.checked });
});

clearBtn.addEventListener("click", async () => {
  await callAction("clear_chat");
});

orbBtn.addEventListener("click", async () => {
  await setOverlayMode("expanded");
});

closeBtn.addEventListener("click", async () => {
  await setOverlayMode("compact");
  await window.assistantApi.hideOverlay();
});

window.addEventListener("keydown", async (event) => {
  if (event.key === "Escape") {
    if (overlayMode === "expanded") {
      await setOverlayMode("compact");
    } else {
      await window.assistantApi.hideOverlay();
    }
  }
});

setControlsEnabled(false);
setOverlayMode("compact");

window.assistantApi.onEvent((message) => {
  const { event, payload, timestamp } = message;
  if (event === "status") {
    setStatus(payload.text || "");
    if (payload.text === "Ready") {
      isReady = true;
      setControlsEnabled(true);
    }
    return;
  }

  if (event === "user_message") {
    appendMessage("you", payload.text || "", timestamp || "");
    return;
  }
  if (event === "assistant_message") {
    appendMessage("assistant", payload.text || "", timestamp || "");
    return;
  }
  if (event === "system_message") {
    appendMessage("system", payload.text || "", timestamp || "");
    return;
  }
  if (event === "chat_cleared") {
    chatBox.innerHTML = "";
    return;
  }
  if (event === "voice_state") {
    const active = Boolean(payload.is_listening);
    startVoiceBtn.disabled = active || !isReady;
    stopVoiceBtn.disabled = !active;
  }
});

window.assistantApi.onOverlayShown(async () => {
  await setOverlayMode("compact");
});
