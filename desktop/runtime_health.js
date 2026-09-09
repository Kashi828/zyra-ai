(() => {
  async function load() {
    try {
      const response = await fetch("/v1/runtime/health");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const health = await response.json();
      document.documentElement.dataset.zyraRuntime = health.runtime;
      document.dispatchEvent(new CustomEvent("zyra:runtime-health", { detail: health }));
      return health;
    } catch (error) {
      document.documentElement.dataset.zyraRuntime = "degraded";
      document.dispatchEvent(new CustomEvent("zyra:runtime-health-error", {
        detail: { message: error.message },
      }));
      return null;
    }
  }

  window.zyraRuntimeHealth = { load };
  load();
  window.setInterval(load, 10000);
})();
