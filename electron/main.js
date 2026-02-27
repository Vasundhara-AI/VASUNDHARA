const { app, BrowserWindow, globalShortcut, ipcMain, screen } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const readline = require("readline");

let mainWindow = null;
let pythonProcess = null;
let requestId = 0;
const pending = new Map();
const WINDOW_DIMENSIONS = {
  compact: { width: 160, height: 160 },
  expanded: { width: 520, height: 700 },
};

function configureWritablePaths() {
  const base =
    process.platform === "win32"
      ? path.join(os.homedir(), "AppData", "Local", "LenovoVoiceAssistantElectron")
      : path.join(app.getPath("home"), ".lenovo-voice-assistant-electron");

  const paths = {
    userData: path.join(base, "user-data"),
    sessionData: path.join(base, "session-data"),
    cache: path.join(base, "cache"),
    crashDumps: path.join(base, "crash-dumps"),
  };

  for (const p of Object.values(paths)) {
    fs.mkdirSync(p, { recursive: true });
  }

  app.setPath("userData", paths.userData);
  app.setPath("sessionData", paths.sessionData);
  app.setPath("cache", paths.cache);
  app.setPath("crashDumps", paths.crashDumps);
}

configureWritablePaths();
app.commandLine.appendSwitch("disable-gpu-shader-disk-cache");
app.commandLine.appendSwitch("disk-cache-dir", app.getPath("cache"));

function resolvePythonCommand() {
  const root = path.join(__dirname, "..");
  if (process.platform === "win32") {
    const venvPython = path.join(root, ".venv", "Scripts", "python.exe");
    if (fs.existsSync(venvPython)) {
      return { command: venvPython, args: [] };
    }
    return { command: "python", args: [] };
  }
  const unixVenvPython = path.join(root, ".venv", "bin", "python");
  if (fs.existsSync(unixVenvPython)) {
    return { command: unixVenvPython, args: [] };
  }
  return { command: "python3", args: [] };
}

function sendToRenderer(channel, payload) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send(channel, payload);
  }
}

function handleServiceMessage(message) {
  if (message.event === "action_result") {
    const actionRequestId = message.payload && message.payload.request_id;
    if (actionRequestId && pending.has(actionRequestId)) {
      const handler = pending.get(actionRequestId);
      pending.delete(actionRequestId);
      handler.resolve(message.payload.result);
    }
    return;
  }

  sendToRenderer("assistant:event", message);
}

function startAssistantService() {
  const python = resolvePythonCommand();
  const servicePath = path.join(__dirname, "..", "assistant_service.py");

  pythonProcess = spawn(python.command, [...python.args, servicePath], {
    cwd: path.join(__dirname, ".."),
    stdio: ["pipe", "pipe", "pipe"],
  });

  const rl = readline.createInterface({ input: pythonProcess.stdout });
  rl.on("line", (line) => {
    if (!line || !line.trim()) {
      return;
    }
    try {
      const data = JSON.parse(line);
      handleServiceMessage(data);
    } catch (err) {
      sendToRenderer("assistant:event", {
        event: "system_message",
        payload: { text: `Bridge parse error: ${err.message}` },
      });
    }
  });

  pythonProcess.stderr.on("data", (chunk) => {
    const text = chunk.toString().trim();
    if (!text) {
      return;
    }
    sendToRenderer("assistant:event", {
      event: "system_message",
      payload: { text: `Python error: ${text}` },
    });
  });

  pythonProcess.on("close", (code) => {
    sendToRenderer("assistant:event", {
      event: "system_message",
      payload: { text: `Assistant service stopped (exit code ${code}).` },
    });
    pythonProcess = null;
  });
}

function sendAction(action, payload = {}) {
  if (!pythonProcess || !pythonProcess.stdin.writable) {
    return Promise.resolve({ ok: false, error: "Assistant service is not running." });
  }

  const id = `req-${Date.now()}-${++requestId}`;
  const message = { action, payload, request_id: id };

  return new Promise((resolve) => {
    pending.set(id, { resolve });
    pythonProcess.stdin.write(`${JSON.stringify(message)}\n`);

    setTimeout(() => {
      if (pending.has(id)) {
        pending.delete(id);
        resolve({ ok: false, error: "Request timed out." });
      }
    }, 120000);
  });
}

function createWindow() {
  const initial = WINDOW_DIMENSIONS.compact;
  mainWindow = new BrowserWindow({
    width: initial.width,
    height: initial.height,
    title: "Windows AI Assistant",
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    maximizable: false,
    minimizable: false,
    fullscreenable: false,
    hasShadow: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  positionWindow(initial.width, initial.height);
  mainWindow.loadFile(path.join(__dirname, "..", "ui", "index.html"));
  mainWindow.hide();
}

function positionWindow(width, height) {
  if (!mainWindow) {
    return;
  }
  const display = screen.getPrimaryDisplay();
  const area = display.workArea;
  const x = Math.round(area.x + area.width / 2 - width / 2);
  const y = Math.round(area.y + area.height - height - 40);
  mainWindow.setBounds({ x, y, width, height }, true);
}

function setOverlayMode(mode) {
  const next = WINDOW_DIMENSIONS[mode] || WINDOW_DIMENSIONS.compact;
  positionWindow(next.width, next.height);
}

function toggleOverlay() {
  if (!mainWindow) {
    return;
  }
  if (mainWindow.isVisible()) {
    mainWindow.hide();
    return;
  }
  setOverlayMode("compact");
  mainWindow.show();
  mainWindow.focus();
  sendToRenderer("overlay:shown", { mode: "compact" });
}

function registerShortcuts() {
  globalShortcut.register("CommandOrControl+Shift+Space", () => {
    toggleOverlay();
  });
}

ipcMain.handle("assistant:action", async (_event, action, payload) => {
  return sendAction(action, payload);
});

ipcMain.handle("overlay:set-mode", async (_event, mode) => {
  setOverlayMode(mode);
  return { ok: true };
});

ipcMain.handle("overlay:hide", async () => {
  if (mainWindow) {
    mainWindow.hide();
  }
  return { ok: true };
});

app.whenReady().then(() => {
  createWindow();
  startAssistantService();
  registerShortcuts();
});

app.on("window-all-closed", () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
});
