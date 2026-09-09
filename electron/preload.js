const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("zyraDesktopBridge", {
  ensureVoiceSession: () => ipcRenderer.invoke("zyra:voice-session"),
  getVoiceAuthHeaders: () => ipcRenderer.invoke("zyra:voice-auth"),
  logoutVoiceSession: () => ipcRenderer.invoke("zyra:voice-logout"),
  ping: () => ipcRenderer.invoke("zyra:ping"),
});
