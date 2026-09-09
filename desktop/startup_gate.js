(() => {
  async function getStartupState() {
    const response = await fetch("/v1/setup/startup");
    if (!response.ok) throw new Error(`Startup state unavailable (${response.status})`);
    return response.json();
  }

  async function applyStartupGate() {
    try {
      const state = await getStartupState();
      document.documentElement.dataset.zyraStartup = state.screen;
      document.dispatchEvent(new CustomEvent("zyra:startup-state", { detail: state }));
    } catch (error) {
      // Fail closed: if setup state cannot be determined, do not claim the workspace is ready.
      document.documentElement.dataset.zyraStartup = "onboarding";
      document.dispatchEvent(new CustomEvent("zyra:startup-error", { detail: { message: error.message } }));
    }
  }

  window.zyraStartup = { getStartupState, applyStartupGate };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyStartupGate, { once: true });
  } else {
    applyStartupGate();
  }
})();
