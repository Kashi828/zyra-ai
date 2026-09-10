(() => {
  const $ = id => document.getElementById(id);

  async function request(path, options = {}) {
    const response = await fetch(path, options);
    if (!response.ok) throw new Error(await response.text());
    return response.status === 204 ? null : response.json();
  }

  function hide(id) { $(id)?.classList.add("hidden"); }
  function show(id) { $(id)?.classList.remove("hidden"); }
  function escape(value) {
    return String(value).replace(/[&<>\"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  }

  async function syncStartup() {
    hide("setup");
    hide("onboarding");
    try {
      const startup = await request("/v1/setup/startup");
      if (startup.screen === "workspace" && !startup.setup_required) return;
      const wizard = await request("/v1/setup/wizard");
      if (wizard.step === "completed" || wizard.completed) return;
      show("setup");
      const check = await request("/v1/system/setup-check");
      if (typeof window.renderSetupChecks === "function") window.renderSetupChecks(check);
      const button = $("setupContinue");
      if (button) button.disabled = !check.ready;
    } catch (error) {
      show("setup");
      const box = $("setupChecks");
      if (box) box.innerHTML = `<div class="setup-repair">ZYRA startup verification failed. ${escape(error.message || error)}</div>`;
      const button = $("setupContinue");
      if (button) button.disabled = true;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    $("setupContinue")?.addEventListener("click", async () => {
      try {
        const check = await request("/v1/system/setup-check");
        if (!check.ready) return;
        await request("/v1/setup/wizard/diagnostics?passed=true", { method: "POST" });
        hide("setup");
        show("onboarding");
        localStorage.setItem("zyra_setup_check_complete", "1");
        localStorage.removeItem("zyra_onboarding_complete");
      } catch (error) {
        const box = $("setupChecks");
        if (box) box.innerHTML = `<div class="setup-repair">Setup could not continue. ${escape(error.message || error)}</div>`;
      }
    });

    $("finishOnboarding")?.addEventListener("click", async () => {
      try {
        const check = await request("/v1/system/setup-check");
        if (!check.ready) throw new Error("Required runtime checks are not ready.");
        await request("/v1/setup/onboarding/complete?diagnostics_passed=true", { method: "POST" });
        localStorage.setItem("zyra_onboarding_complete", "1");
        hide("onboarding");
        document.documentElement.dataset.zyraStartup = "workspace";
      } catch (error) {
        const step = $("obStep3");
        if (step) {
          step.querySelector(".setup-repair")?.remove();
          const message = document.createElement("p");
          message.className = "setup-repair";
          message.textContent = `Setup could not finish: ${error.message || error}`;
          step.appendChild(message);
        }
      }
    });

    setTimeout(syncStartup, 50);
  }, { once: true });
})();
