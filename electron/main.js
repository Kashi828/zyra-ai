const { app, BrowserWindow, ipcMain, session } = require("electron");
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");
const http = require("http");

let mainWindow = null;
let bridge = null;
let backend = null;
let backendRestarts = 0;
const MAX_BACKEND_RESTARTS = 2;

function bundledExecutable(name) {
  if (!app.isPackaged) return null;
  const exe = process.platform === "win32" ? `${name}.exe` : name;
  const candidate = path.join(process.resourcesPath, "runtime", name, exe);
  return fs.existsSync(candidate) ? candidate : null;
}

function pythonExecutable() {
  if (process.env.ZYRA_PYTHON) return process.env.ZYRA_PYTHON;
  return process.platform === "win32" ? "python" : "python3";
}

function waitForBackend(attempts = 60, delayMs = 250) {
  return new Promise((resolve, reject) => {
    let tries = 0;
    const check = () => {
      const req = http.get("http://127.0.0.1:8000/health", {timeout: 1000}, res => {
        let body = "";
        res.on("data", chunk => body += chunk);
        res.on("end", () => {
          if (res.statusCode === 200) {
            try {
              const data = JSON.parse(body);
              if (data.ok) return resolve(data);
            } catch (_) {}
          }
          retry();
        });
      });
      req.on("error", retry);
      req.on("timeout", () => { req.destroy(); retry(); });
    };
    const retry = () => {
      tries += 1;
      if (tries >= attempts) reject(new Error("ZYRA backend health check timed out"));
      else setTimeout(check, delayMs);
    };
    check();
  });
}

function runtimeEnvironment() {
  const userData = app.getPath("userData");
  const dataDir = path.join(userData, "data");
  fs.mkdirSync(dataDir, {recursive: true});
  return {
    ...process.env,
    ZYRA_DB_PATH: path.join(dataDir, "zyra_security.sqlite3"),
  };
}

function startBackend() {
  if (process.env.ZYRA_SKIP_BACKEND === "1") return;
  const bundled = bundledExecutable("zyra-backend");
  const env = runtimeEnvironment();
  if (bundled) {
    backend = spawn(bundled, [], {
      cwd: app.getPath("userData"),
      windowsHide: true,
      stdio: "ignore",
      env,
    });
  } else {
    backend = spawn(pythonExecutable(), ["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"], {
      cwd: path.resolve(__dirname, ".."),
      windowsHide: true,
      stdio: "ignore",
      env,
    });
  }
  backend.on("error", () => { backend = null; });
  backend.on("exit", () => {
    backend = null;
    if (!mainWindow || backendRestarts >= MAX_BACKEND_RESTARTS) return;
    backendRestarts += 1;
    setTimeout(() => startBackend(), 500);
  });
}

function startNativeBridge() {
  if (process.env.ZYRA_SKIP_NATIVE_BRIDGE === "1") return;
  const bundled = bundledExecutable("zyra-native-bridge");
  if (bundled) {
    bridge = spawn(bundled, [], {
      cwd: app.getPath("userData"),
      windowsHide: true,
      stdio: ["pipe", "pipe", "ignore"],
      env: runtimeEnvironment(),
    });
  } else {
    bridge = spawn(pythonExecutable(), ["-m", "desktop.native_bridge"], {
      cwd: path.resolve(__dirname, ".."),
      windowsHide: true,
      stdio: ["pipe", "pipe", "ignore"],
      env: runtimeEnvironment(),
    });
  }
  bridge.on("error", () => { bridge = null; });
}

function rpc(method, args = {}) {
  return new Promise((resolve, reject) => {
    if (!bridge || !bridge.stdin.writable || !bridge.stdout.readable) {
      reject(new Error("desktop native bridge unavailable"));
      return;
    }
    const request = JSON.stringify({method, ...args}) + "\n";
    let buffer = "";
    const onData = chunk => {
      buffer += chunk.toString();
      const newline = buffer.indexOf("\n");
      if (newline < 0) return;
      const line = buffer.slice(0, newline);
      cleanup();
      try {
        const result = JSON.parse(line);
        if (result.ok === false) reject(new Error(result.error || "native bridge error"));
        else resolve(result);
      } catch (error) { reject(error); }
    };
    const timer = setTimeout(() => { cleanup(); reject(new Error("native bridge timeout")); }, 5000);
    const cleanup = () => {
      clearTimeout(timer);
      bridge?.stdout?.off("data", onData);
    };
    bridge.stdout.on("data", onData);
    bridge.stdin.write(request);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 980,
    minHeight: 680,
    backgroundColor: "#0b0d12",
    title: "ZYRA AI",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  mainWindow.loadFile(path.join(__dirname, "..", "desktop", "index.html"));
  mainWindow.on("closed", () => { mainWindow = null; });
}

function registerIpc() {
  ipcMain.handle("zyra:voice-session", async () => rpc("voice.session.ensure"));
  ipcMain.handle("zyra:voice-auth", async () => rpc("voice.auth.headers"));
  ipcMain.handle("zyra:voice-logout", async () => rpc("voice.logout"));
  ipcMain.handle("zyra:ping", async () => rpc("ping"));
}

app.whenReady().then(async () => {
  session.defaultSession.setPermissionRequestHandler((_webContents, permission, callback) => {
    callback(permission === "media");
  });
  registerIpc();
  startBackend();
  startNativeBridge();
  try { await waitForBackend(); } catch (error) { console.error(error.message); }
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (backend) backend.kill();
  if (bridge) bridge.kill();
  if (process.platform !== "darwin") app.quit();
});

// ZYRA_STARTUP_GATE: packaged builds prefer the bundled local runtime; development
// builds retain the Python fallback. The renderer remains sandboxed and local-first.
