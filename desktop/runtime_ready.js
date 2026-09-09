(() => {
  async function load() {
    try {
      const response = await fetch("/v1/setup/runtime-ready");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const state = await response.json();
      document.documentElement.dataset.zyraRuntimeReady = state.ready ? "true" : "false";
      document.dispatchEvent(new CustomEvent("zyra:runtime-ready", { detail: state }));
      return state;
    } catch (error) {
      document.documentElement.dataset.zyraRuntimeReady = "false";
      document.dispatchEvent(new CustomEvent("zyra:runtime-error", { detail: { message: error.message } }));
      return null;
    }
  }

  async function context() {
    const response = await fetch("/v1/setup/workspace-context");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    document.dispatchEvent(new CustomEvent("zyra:workspace-context", { detail: data }));
    return data;
  }

  window.zyraRuntime = { load, context };
})();
