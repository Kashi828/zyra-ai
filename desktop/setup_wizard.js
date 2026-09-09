(() => {
  const state = {
    step: "diagnostics",
    ready: false,
  };

  async function request(path, options = {}) {
    const response = await fetch(path, options);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async function load() {
    const status = await request("/v1/setup/wizard");
    state.step = status.step;
    state.ready = Boolean(status.diagnostics_passed);
    document.documentElement.dataset.zyraSetupStep = status.step;
    document.dispatchEvent(new CustomEvent("zyra:setup-step", { detail: status }));
    return status;
  }

  async function markDiagnostics(passed) {
    const status = await request(
      `/v1/setup/wizard/diagnostics?passed=${passed ? "true" : "false"}`,
      { method: "POST" }
    );
    state.step = status.step;
    state.ready = Boolean(status.diagnostics_passed);
    document.documentElement.dataset.zyraSetupStep = status.step;
    document.dispatchEvent(new CustomEvent("zyra:setup-step", { detail: status }));
    return status;
  }

  async function complete() {
    const status = await request("/v1/setup/wizard/complete", { method: "POST" });
    document.documentElement.dataset.zyraSetupStep = status.step;
    document.dispatchEvent(new CustomEvent("zyra:setup-complete", { detail: status }));
    return status;
  }

  async function reset() {
    const status = await request("/v1/setup/wizard/reset", { method: "POST" });
    document.documentElement.dataset.zyraSetupStep = status.step;
    document.dispatchEvent(new CustomEvent("zyra:setup-step", { detail: status }));
    return status;
  }

  window.zyraSetupWizard = { load, markDiagnostics, complete, reset };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", load, { once: true });
  } else {
    load();
  }
})();
