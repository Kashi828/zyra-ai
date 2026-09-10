(() => {
  // The desktop previously had two independent first-run systems:
  // localStorage in app.js and persistent server-side setup state. That could
  // display conflicting overlays or let a stale browser flag bypass setup.
  // This controller makes the server-side state authoritative and keeps the
  // setup diagnostics screen before onboarding.
  const $ = id => document.getElementById(id);

  async function get(path, options = {}) {
    const response = await fetch(path, options);
    if (!response.ok) throw new Error(await response.text());
    return response.status === 204 ? null : response.json();
  }

  function hide(id) {
    $(id)?.classList.add("hidden");
  }

  function show(id) {
    $(id)?.classList.remove("hidden");
  }

  async function syncStartup() {
    hide("setup");
    hide("onboarding");

    try {
      const startup = await get("/v1/setup/startup");
      if (startup.screen === "workspace" && !startup.setup_required) {
        return;
      }

      const wizard = await get("/v1/setup/wizard");
      if (wizard.step === "completed" || wizard.completed) {
        return;
      }

      // Always run the local, non-destructive diagnostics before onboarding.
      show("setup");
      const button = $("setupContinue");
      if (button) button.disabled = true;

      const check = await get("/v1/system/setup-check");
      if (typeof window.renderSetupChecks === "function") {
        window.renderSetupChecks(check);
      }
      if (check.ready) {
        await get("/v1/setup/wizard/diagnostics?passed=true", { method: "POST" });
        if (button) button.disabled = false;
      }
    } catch (error) {
      // Keep the setup screen visible and fail closed. Never fall through to
      // the workspace when startup state cannot be established.
      show("setup");
      const box = $("setupChecks");
      if (box) box.innerHTML = `<div class="setup-repair">ZYRA startup verification failed. ${String(error.message || error).replace(/[&<>\"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]))}</div>`;
      const button = $("setupContinue");
      if (button) button.disabled = true;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const continueButton = $("setupContinue");
    if (continueButton) {
      continueButton.addEventListener("click", async () => {
        try {
          const check = await get("/v1/system/setup-check");
          if (!check.ready) return;
          await get("/v1/setup/wizard/diagnostics?passed=true", { method: "POST" });
          await get("/v1/setup/wizard/complete", { method: "POST" });
          hide("setup");
          if (localStorage) localStorage.setItem("zyra_setup_check_complete", "1");
          if (localStorage) localStorage.removeItem("zyra_onboarding_complete");
          show("onboarding");
        } catch (_) {
          // Existing app.js feedback remains visible when completion fails.
        }
      });
    }

    // Let app.js finish binding first, then make the authoritative state win.
    setTimeout(syncStartup, 0);
  }, { once: true });
})();
