(() => {
  async function request(path, options = {}) {
    const response = await fetch(path, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
    return data;
  }

  window.zyraConfigurationProfiles = {
    list: () => request("/v1/setup/configuration/profiles"),
    apply: (name) => request(`/v1/setup/configuration/profiles/${encodeURIComponent(name)}`, { method: "POST" }),
    validate: () => request("/v1/setup/configuration/validate"),
  };
})();
