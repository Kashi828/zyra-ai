(() => {
  async function loadConfigurationStatus() {
    try {
      const response = await fetch("/v1/setup/configuration/status");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const status = await response.json();
      document.dispatchEvent(new CustomEvent("zyra:configuration-status", { detail: status }));
      return status;
    } catch (error) {
      document.dispatchEvent(
        new CustomEvent("zyra:configuration-status-error", { detail: { message: error.message } })
      );
      return null;
    }
  }

  window.zyraConfigurationStatus = { load: loadConfigurationStatus };
})();
