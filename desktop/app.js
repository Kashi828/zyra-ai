const state = { taskId: null, poller: null, section: "assistant", lastSpokenStatus: null };

const setupState = { ready: false, loaded: false };

function renderSetupChecks(data) {
  const box = $("setupChecks");
  if (!box) return;
  const checks = data?.checks || [];
  box.innerHTML = checks.map(item => {
    const stateClass = item.ok ? "ok" : (item.required ? "bad" : "optional");
    const label = item.ok ? "READY" : (item.required ? "REQUIRED" : "OPTIONAL");
    return `<div class="setup-item"><div><b>${escapeHtml(item.label)}</b><small>${escapeHtml(item.detail)}</small></div><span class="setup-state ${stateClass}">${label}</span></div>`;
  }).join("") || `<div class="setup-loading">No diagnostic data returned.</div>`;
  if (!data?.ready) {
    box.insertAdjacentHTML("beforeend", `<div class="setup-repair">Required runtime checks are not ready. Install or repair the missing components using the Windows preparation instructions, then run the check again.</div>`);
  }
  setupState.ready = !!data?.ready;
  setupState.loaded = true;
  const btn = $("setupContinue");
  if (btn) btn.disabled = !setupState.ready;
}

async function runSetupCheck() {
  const box = $("setupChecks");
  if (box) box.innerHTML = `<div class="setup-loading">Checking your PC…</div>`;
  try {
    const data = await api("/v1/system/setup-check");
    renderSetupChecks(data);
  } catch (e) {
    setupState.ready = false;
    setupState.loaded = true;
    if (box) box.innerHTML = `<div class="setup-repair">ZYRA backend is not ready yet. ${escapeHtml(e.message)}</div>`;
    const btn = $("setupContinue");
    if (btn) btn.disabled = true;
  }
}

function finishSetup() {
  if (!setupState.ready) return;
  localStorage.setItem("zyra_setup_check_complete", "1");
  $("setup")?.classList.add("hidden");
}

function showSetup() {
  const setup = $("setup");
  if (!setup) return;
  setup.classList.remove("hidden");
  runSetupCheck();
}

const $ = (id) => document.getElementById(id);
const sections = ["assistant","tasks","devices","permissions","settings"];

function setSection(name) {
  if (!sections.includes(name)) return;
  state.section = name;
  document.querySelectorAll("[data-section]").forEach(btn =>
    btn.classList.toggle("active", btn.dataset.section === name)
  );
  document.querySelectorAll(".page").forEach(page =>
    page.classList.toggle("visible", page.id === `page-${name}`)
  );
  loadState();
}

async function api(path, options={}) {
  const r = await fetch(path, {
    headers: {"Content-Type":"application/json", ...(options.headers || {})},
    ...options
  });
  if (!r.ok) throw new Error(await r.text());
  return r.status === 204 ? null : r.json();
}

function setActivity(text, ok=false) {
  const el = $("activity");
  el.innerHTML = `<span>${ok ? "✓" : "●"}</span> ${text}`;
}

async function createTask() {
  const goal = $("goal").value.trim();
  if (!goal) return setActivity("Enter a goal first.");
  setActivity("Submitting task...");
  try {
    const data = await api("/v1/runtime/tasks", {
      method: "POST",
      body: JSON.stringify({goal})
    });
    state.taskId = data.task_id;
    setActivity(`Task queued · ${state.taskId.slice(0, 10)}`, true);
    watchTask();
    setSection("tasks");
  } catch (e) {
    setActivity(`Task submission failed: ${e.message}`);
  }
}


function speakStatus(status, taskId) {
  const key = `${taskId || ""}:${status || ""}`;
  if (state.lastSpokenStatus === key || !window.speechSynthesis) return;
  state.lastSpokenStatus = key;
  const phrases = {
    queued: "I queued your task.",
    planning: "I am planning that now.",
    running: "I am working on it.",
    awaiting_approval: "I need your approval before I continue.",
    completed: "Your task is complete.",
    failed: "Your task could not be completed.",
    cancelled: "Your task was cancelled.",
  };
  const text = phrases[status];
  if (!text) return;
  try {
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
  } catch (_) {}
}

async function watchTask() {
  if (!state.taskId) return;
  if (state.poller) clearInterval(state.poller);
  state.poller = setInterval(async () => {
    try {
      const data = await api("/v1/runtime/state");
      const task = data.active_tasks?.[state.taskId];
      if (!task) return;
      const detail = task.detail ? ` · ${task.detail}` : "";
      setActivity(`${task.status}${detail}`, task.status === "completed");
      speakStatus(task.status, state.taskId);
      renderTasks(data);
      if (["completed","failed"].includes(task.status)) clearInterval(state.poller);
    } catch (_) {}
  }, 1000);
}

function renderTasks(data) {
  const box = $("taskList");
  const tasks = Object.entries(data.active_tasks || {});
  box.innerHTML = tasks.length
    ? tasks.map(([id,t]) => `
      <div class="list-item">
        <div><b>${escapeHtml(t.goal)}</b><small>${escapeHtml(id.slice(0,12))}</small></div>
        <strong class="${t.status}">${escapeHtml(t.status)}</strong>
      </div>`).join("")
    : `<div class="empty">No tasks yet.</div>`;
}

function renderDevices(data) {
  const devices = data.connected_devices || [];
  $("deviceList").innerHTML = devices.length
    ? devices.map(d => `<div class="list-item"><div><b>${escapeHtml(d)}</b><small>Connected</small></div><strong class="online">ONLINE</strong></div>`).join("")
    : `<div class="empty">No connected devices.</div>`;
  $("deviceSummary").textContent = `${devices.length} connected device${devices.length===1?"":"s"}`;
}

async function loadState() {
  try {
    const data = await api("/v1/runtime/state");
    renderTasks(data);
    renderDevices(data);
  } catch (_) {
    $("deviceSummary").textContent = "Backend offline";
  }
}

async function stopAgent() {
  try {
    const r = await api("/v1/agent/stop", {method:"POST"});
    setActivity(r.ok ? "Agent stop requested." : "Stop request failed.", r.ok);
  } catch (e) {
    setActivity(`Stop request failed: ${e.message}`);
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[c]));
}

document.querySelectorAll("[data-section]").forEach(btn =>
  btn.addEventListener("click", () => setSection(btn.dataset.section))
);
$("runTask").addEventListener("click", createTask);
$("stopAgent").addEventListener("click", stopAgent);
$("goal").addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") createTask();
});
loadState();
setSection("assistant");

$("setupRefresh")?.addEventListener("click", runSetupCheck);
$("setupContinue")?.addEventListener("click", finishSetup);
if (localStorage.getItem("zyra_setup_check_complete") !== "1") showSetup();

const onboarding = $("onboarding");
const ob1 = $("obStep1"), ob2 = $("obStep2"), ob3 = $("obStep3");
function showOnboarding(){ onboarding.classList.remove("hidden"); }
function finishOnboarding(){ localStorage.setItem("zyra_onboarding_complete","1"); onboarding.classList.add("hidden"); }
$("chooseLocal")?.addEventListener("click",()=>{ob1.classList.add("hidden");ob2.classList.remove("hidden");});
$("startPairing")?.addEventListener("click",()=>{ob2.classList.add("hidden");ob3.classList.remove("hidden");});
$("skipPairing")?.addEventListener("click",()=>{ob2.classList.add("hidden");ob3.classList.remove("hidden");});
$("finishOnboarding")?.addEventListener("click",finishOnboarding);
if(localStorage.getItem("zyra_onboarding_complete")!=="1") showOnboarding();

async function startPairing(){
  const el=document.getElementById("pairStatus");
  if(!el) return;
  el.textContent="Preparing secure pairing offer...";
  try{
    const r=await api("/v1/devices/pairing/offer",{method:"POST"});
    el.textContent=r.offer?`Offer ready · ${r.offer.pc_name} · ${r.offer.fingerprint}`:"Pairing service unavailable.";
  }catch(e){el.textContent=`Pairing unavailable: ${e.message}`;}
}
document.getElementById("pairDevice")?.addEventListener("click",startPairing);


// Voice input — browser/desktop speech recognition adapter.
// It only writes a transcript into the existing goal box; execution still
// happens through the normal ZYRA task workflow.
const voice = {
  recognition: null,
  listening: false,
  finalText: "",
};

function setVoiceStatus(text) {
  const el = $("voiceStatus");
  if (el) el.textContent = text;
}

function setVoiceMeter(active) {
  const el = $("voiceMeter");
  if (el) el.classList.toggle("active", !!active);
}

function setupVoice() {
  const panel = $("voicePanel");
  const toggle = $("voiceButton");
  const start = $("voiceStart");
  const stop = $("voiceStop");
  const language = $("voiceLanguage");
  if (!panel || !toggle || !start || !stop || !language) return;

  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    toggle.title = "Speech recognition is unavailable in this desktop runtime";
    setVoiceStatus("Speech recognition unavailable — type your goal instead");
    start.disabled = true;
    return;
  }

  const recognition = new Recognition();
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.maxAlternatives = 1;
  voice.recognition = recognition;

  recognition.onstart = () => {
    voice.listening = true;
    voice.finalText = "";
    start.disabled = true;
    stop.disabled = false;
    toggle.classList.add("active");
    setVoiceMeter(true);
    setVoiceStatus("Listening…");
  };

  recognition.onresult = (event) => {
    let interim = "";
    let finalText = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const text = event.results[i][0].transcript;
      if (event.results[i].isFinal) finalText += text;
      else interim += text;
    }
    if (finalText) voice.finalText += finalText + " ";
    $("goal").value = (voice.finalText + interim).trim();
    setVoiceStatus(interim ? `Hearing: ${interim}` : "Processing…");
  };

  recognition.onerror = (event) => {
    const messages = {
      "not-allowed": "Microphone permission denied",
      "audio-capture": "No microphone was available",
      "network": "Speech service is unavailable",
      "aborted": "Listening stopped",
    };
    setVoiceStatus(messages[event.error] || `Voice error: ${event.error}`);
  };

  recognition.onend = () => {
    voice.listening = false;
    start.disabled = false;
    stop.disabled = true;
    toggle.classList.remove("active");
    setVoiceMeter(false);
    if ($("goal").value.trim()) {
      setVoiceStatus("Transcript ready — review before running");
    } else if (!voice.recognition) {
      setVoiceStatus("Ready to listen");
    } else {
      setVoiceStatus("No speech captured");
    }
  };

  const begin = () => {
    recognition.lang = language.value;
    try {
      recognition.start();
    } catch (e) {
      setVoiceStatus("Voice input is already starting");
    }
  };

  const end = () => {
    try { recognition.stop(); } catch (_) {}
  };

  toggle.addEventListener("click", () => {
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden")) $("goal").focus();
  });
  if (!(navigator.mediaDevices?.getUserMedia && window.MediaRecorder)) {
    start.addEventListener("click", begin);
    stop.addEventListener("click", end);
  }
  language.addEventListener("change", () => {
    if (voice.listening) {
      end();
      setTimeout(begin, 150);
    }
  });
}
setupVoice();


async function ensureDesktopVoiceSession() {
  // Packaged Windows shells can expose the native bridge. Refresh tokens stay
  // inside the native runtime and never enter browser localStorage.
  if (window.zyraDesktopBridge?.ensureVoiceSession) {
    const nativeState = await window.zyraDesktopBridge.ensureVoiceSession();
    return {
      device_id: nativeState.device_id,
      session_id: nativeState.session_id,
      expires_at: nativeState.expires_at,
    };
  }

  const existing = {
    device_id: localStorage.getItem("zyra_voice_device_id"),
    session_id: localStorage.getItem("zyra_voice_session_id"),
  };
  if (existing.device_id && existing.session_id) return existing;

  const data = await api("/v1/voice/desktop/bootstrap",{method:"POST"});
  localStorage.setItem("zyra_voice_device_id", data.device_id);
  localStorage.setItem("zyra_voice_session_id", data.session_id);
  // Never persist the refresh token in the browser.
  return {device_id:data.device_id, session_id:data.session_id};
}

async function transcribeLocalRecording(blob) {
  const session = await ensureDesktopVoiceSession();
  let authHeaders = {
    "X-ZYRA-Device-Id": session.device_id,
    "Authorization": `Bearer ${session.session_id}`,
  };
  if (window.zyraDesktopBridge?.getVoiceAuthHeaders) {
    try {
      const nativeAuth = await window.zyraDesktopBridge.getVoiceAuthHeaders();
      if (nativeAuth?.headers) authHeaders = {...authHeaders, ...nativeAuth.headers};
    } catch (_) {}
  }
  const r = await fetch("/v1/voice/transcribe", {
    method: "POST",
    headers: {
      "Content-Type": blob.type || "audio/webm",
      ...authHeaders,
    },
    body: blob,
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function setupDirectLocalMic() {
  const start = $("voiceStart");
  const stop = $("voiceStop");
  if (!start || !stop || !navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) return;

  let recorder = null;
  let chunks = [];
  let audioContext = null;
  let analyser = null;
  let meterTimer = null;
  let speechStartedAt = 0;
  let lastSpeechAt = 0;
  const silenceMs = 1200;
  const threshold = 0.022;

  start.addEventListener("click", async () => {
    try {
      setVoiceStatus("Requesting microphone…");
      const stream = await navigator.mediaDevices.getUserMedia({audio:true});
      chunks = [];
      try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(stream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 1024;
        source.connect(analyser);
      } catch (_) {
        audioContext = null;
        analyser = null;
      }
      const mimeCandidates = ["audio/webm;codecs=opus","audio/webm","audio/ogg;codecs=opus"];
      const mimeType = mimeCandidates.find(t => MediaRecorder.isTypeSupported(t)) || "";
      recorder = new MediaRecorder(stream, mimeType ? {mimeType} : undefined);

      recorder.ondataavailable = e => { if (e.data?.size) chunks.push(e.data); };
      recorder.onstart = () => {
        $("voiceStart").disabled = true;
        $("voiceStop").disabled = false;
        setVoiceMeter(true);
        setVoiceStatus("Listening locally…");
      };
      recorder.onstop = async () => {
        if (meterTimer) clearInterval(meterTimer);
        meterTimer = null;
        if (audioContext) {
          try { await audioContext.close(); } catch (_) {}
        }
        audioContext = null;
        analyser = null;
        stream.getTracks().forEach(t => t.stop());
        $("voiceStart").disabled = false;
        $("voiceStop").disabled = true;
        setVoiceMeter(false);
        setVoiceStatus("Transcribing locally…");
        try {
          const blob = new Blob(chunks, {type: recorder.mimeType || "audio/webm"});
          const result = await transcribeLocalRecording(blob);
          $("goal").value = result.text || "";
          setVoiceStatus(result.text ? "Local transcript ready — review before running" : "No speech detected");
        } catch (e) {
          setVoiceStatus(`Local voice failed: ${e.message}`);
        }
      };
      recorder.start();
      speechStartedAt = performance.now();
      lastSpeechAt = performance.now();
      if (analyser) {
        const samples = new Uint8Array(analyser.fftSize);
        meterTimer = setInterval(() => {
          if (!analyser || !recorder || recorder.state === "inactive") return;
          analyser.getByteTimeDomainData(samples);
          let sum = 0;
          for (const x of samples) {
            const v = (x - 128) / 128;
            sum += v * v;
          }
          const rms = Math.sqrt(sum / samples.length);
          if (rms >= threshold) lastSpeechAt = performance.now();
          const elapsed = performance.now() - speechStartedAt;
          if (elapsed > 500 && performance.now() - lastSpeechAt >= silenceMs) {
            setVoiceStatus("Silence detected — stopping");
            recorder.stop();
          }
        }, 80);
      }
    } catch (e) {
      if (meterTimer) clearInterval(meterTimer);
      meterTimer = null;
      setVoiceStatus(`Microphone unavailable: ${e.message}`);
    }
  });

  stop.onclick = () => {
    if (recorder && recorder.state !== "inactive") recorder.stop();
  };
}

// Prefer direct local microphone capture when available. The Mission 77
// SpeechRecognition implementation remains as a fallback for runtimes where
// MediaRecorder/getUserMedia are unavailable.
if (navigator.mediaDevices?.getUserMedia && window.MediaRecorder) {
  setupDirectLocalMic();
}
