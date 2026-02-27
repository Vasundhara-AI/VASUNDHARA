const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("assistantApi", {
  sendAction: (action, payload) => ipcRenderer.invoke("assistant:action", action, payload),
  setOverlayMode: (mode) => ipcRenderer.invoke("overlay:set-mode", mode),
  hideOverlay: () => ipcRenderer.invoke("overlay:hide"),
  onEvent: (handler) => {
    const wrapped = (_event, data) => handler(data);
    ipcRenderer.on("assistant:event", wrapped);
    return () => ipcRenderer.removeListener("assistant:event", wrapped);
  },
  onOverlayShown: (handler) => {
    const wrapped = (_event, data) => handler(data);
    ipcRenderer.on("overlay:shown", wrapped);
    return () => ipcRenderer.removeListener("overlay:shown", wrapped);
  },
});
