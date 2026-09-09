(() => {
  const panel = document.getElementById("zyra-onboarding");
  if (!panel) return;

  const checks = {
    backend: panel.querySelector('[data-check="backend"] strong'),
    python: panel.querySelector('[data-check="python"] strong'),
    voice: panel.querySelector('[data-check="voice"] strong'),
  };
  const recheck = document.getElementById("zyra-setup-recheck");
  const continueButton = document.getElementById("zyra-setup-continue");
  const message = document.getElementById("zyra-setup-message");

  async function getJson(path, options = {}) {
    const response = await fetch(path, options);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  function setCheck(node, value) {
    if (node) node.textContent = value;
  }

  async function run() {
    panel.hidden = false;
    continueButton.disabled = true;
    message.textContent = "Running local checks…";

    try {
      const [diag, state] = await Promise.all([
        getJson("/v1/system/diagnostics"),
        getJson("/v1/setup/onboarding"),
      ]);

      const backendOk = Boolean(diag.backend ?? diag.fastapi ?? true);
      const pythonOk = Boolean(diag.python ?? true);
      const voice = diag.voice ?? diag.optional_voice ?? "Optional";

      setCheck(checks.backend, backendOk ? "Ready" : "Unavailable");
      setCheck(checks.python, pythonOk ? "Ready" : "Unavailable");
      setCheck(checks.voice, typeof voice === "boolean" ? (voice ? "Ready" : "Optional") : String(voice));

      const ready = backendOk && pythonOk;
      continueButton.disabled = !ready;
      message.textContent = ready
        ? (state.completed ? "Setup already complete." : "Your system is ready.")
        : "Fix the required checks, then run Recheck.";
    } catch (error) {
      setCheck(checks.backend, "Unavailable");
      setCheck(checks.python, "Unavailable");
      continueButton.disabled = true;
      message.textContent = `Setup check failed: ${error.message}`;
    }
  }

  recheck?.addEventListener("click", run);
  continueButton?.addEventListener("click", async () => {
    continueButton.disabled = true;
    try {
      await getJson("/v1/setup/onboarding/complete", { method: "POST" });
      panel.hidden = true;
      document.dispatchEvent(new CustomEvent("zyra:onboarding-complete"));
    } catch (error) {
      message.textContent = `Could not finish setup: ${error.message}`;
      continueButton.disabled = false;
    }
  });

  run();
})();
