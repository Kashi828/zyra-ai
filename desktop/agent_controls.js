(() => {
  const button = document.getElementById("stopAgent");
  if (!button) return;
  let stopped = false;
  button.addEventListener("dblclick", async (event) => {
    event.preventDefault();
    if (!stopped) return;
    try {
      const r = await fetch("/v1/agent/resume", {method: "POST"});
      if (!r.ok) throw new Error(await r.text());
      stopped = false;
      button.textContent = "Stop Agent";
      button.classList.remove("resume");
    } catch (e) {
      const activity = document.getElementById("activity");
      if (activity) activity.textContent = `Resume failed: ${e.message}`;
    }
  });
})();
