const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("zyraDesktopBridge", {
  ensureVoiceSession: () => ipcRenderer.invoke("zyra:voice-session"),
  getVoiceAuthHeaders: () => ipcRenderer.invoke("zyra:voice-auth"),
  logoutVoiceSession: () => ipcRenderer.invoke("zyra:voice-logout"),
  getAuthContext: () => ipcRenderer.invoke("zyra:auth-context"),
  ping: () => ipcRenderer.invoke("zyra:ping"),
});
