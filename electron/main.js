const { app, BrowserWindow, ipcMain, session, safeStorage } = require("electron");
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");
const http = require("http");

let mainWindow = null;
let bridge = null;
let backend = null;
let backendRestarts = 0;
let authPromise = null;
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
    const retry = () => {
      tries += 1;
      if (tries >= attempts) reject(new Error("ZYRA backend health check timed out"));
      else setTimeout(check, delayMs);
    };
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
  const host = process.env.ZYRA_BIND_HOST || (app.isPackaged ? "0.0.0.0" : "127.0.0.1");
  if (bundled) {
    backend = spawn(bundled, ["--host", host], {
      cwd: app.getPath("userData"),
      windowsHide: true,
      stdio: "ignore",
      env,
    });
  } else {
    backend = spawn(pythonExecutable(), ["-m", "uvicorn", "main:app", "--host", host, "--port", "8000"], {
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

function authFile() {
  return path.join(app.getPath("userData"), "auth-state.bin");
}

function loadAuthState() {
  try {
    const raw = fs.readFileSync(authFile());
    if (!safeStorage.isEncryptionAvailable()) return null;
    const text = safeStorage.decryptString(raw);
    return JSON.parse(text);
  } catch (_) {
    return null;
  }
}

function saveAuthState(state) {
  if (!safeStorage.isEncryptionAvailable()) {
    throw new Error("Windows secure credential storage is unavailable");
  }
  const encrypted = safeStorage.encryptString(JSON.stringify(state));
  fs.writeFileSync(authFile(), encrypted, {mode: 0o600});
}

function requestJson(urlPath, method, body) {
  return new Promise((resolve, reject) => {
    const payload = body ? Buffer.from(JSON.stringify(body)) : null;
    const req = http.request({
      hostname: "127.0.0.1",
      port: 8000,
      path: urlPath,
      method,
      headers: payload ? {"Content-Type": "application/json", "Content-Length": payload.length} : {},
      timeout: 5000,
    }, res => {
      let text = "";
      res.on("data", chunk => text += chunk);
      res.on("end", () => {
        let parsed = {};
        try { parsed = text ? JSON.parse(text) : {}; } catch (_) { parsed = {detail: text}; }
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(parsed);
        else reject(new Error(parsed.detail || `HTTP ${res.statusCode}`));
      });
    });
    req.on("error", reject);
    req.on("timeout", () => req.destroy(new Error("local API timeout")));
    if (payload) req.write(payload);
    req.end();
  });
}

async function ensureAuthContext() {
  if (authPromise) return authPromise;
  authPromise = (async () => {
    let state = loadAuthState();
    const now = Math.floor(Date.now() / 1000);
    if (state?.device_id && state?.session_id && state?.refresh_token && Number(state.expires_at || 0) > now + 60) {
      return {device_id: state.device_id, session_id: state.session_id};
    }

    if (state?.device_id && state?.refresh_token) {
      try {
        const refreshed = await requestJson("/v1/session/refresh", "POST", {
          device_id: state.device_id,
          refresh_token: state.refresh_token,
        });
        state = {...state, ...refreshed};
        saveAuthState(state);
        return {device_id: state.device_id, session_id: state.session_id};
      } catch (_) {}
    }

    if (state?.device_id && state?.device_secret) {
      try {
        const created = await requestJson("/v1/session/create", "POST", {
          device_id: state.device_id,
          device_secret: state.device_secret,
        });
        state = {...state, ...created};
        saveAuthState(state);
        return {device_id: state.device_id, session_id: state.session_id};
      } catch (_) {}
    }

    const bootstrap = await requestJson("/v1/local/bootstrap", "POST", {});
    saveAuthState(bootstrap);
    return {device_id: bootstrap.device_id, session_id: bootstrap.session_id};
  })().finally(() => { authPromise = null; });
  return authPromise;
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
  ipcMain.handle("zyra:auth-context", async () => ensureAuthContext());
  ipcMain.handle("zyra:ping", async () => rpc("ping"));
}

app.whenReady().then(async () => {
  session.defaultSession.setPermissionRequestHandler((_webContents, permission, callback) => {
    callback(permission === "media");
  });
  registerIpc();
  startBackend();
  startNativeBridge();
  try { await waitForBackend(); await ensureAuthContext(); } catch (error) { console.error(error.message); }
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
// builds retain the Python fallback. Credentials stay in Electron safeStorage.
