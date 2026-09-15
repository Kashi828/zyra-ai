(() => {
  const workspaceSections = ["assistant", "builder", "console", "tasks", "devices", "permissions", "settings"];

  function openWorkspaceSection(name) {
    if (!workspaceSections.includes(name)) return;
    document.querySelectorAll("[data-section]").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.section === name);
    });
    document.querySelectorAll(".page").forEach(page => {
      page.classList.toggle("visible", page.id === `page-${name}`);
    });
    if (name === "console") refreshConsole();
  }

  document.querySelectorAll("[data-section=builder], [data-section=console]").forEach(btn => {
    btn.addEventListener("click", event => {
      event.preventDefault();
      openWorkspaceSection(btn.dataset.section);
    });
  });

  document.getElementById("openBuilder")?.addEventListener("click", () => {
    openWorkspaceSection("builder");
    document.getElementById("builderGoal")?.focus();
  });

  document.getElementById("openConsole")?.addEventListener("click", () => {
    openWorkspaceSection("console");
  });

  async function previewPlan() {
    const goal = document.getElementById("builderGoal")?.value.trim();
    const output = document.getElementById("planPreview");
    if (!goal) {
      if (output) output.textContent = "Describe a goal first.";
      return;
    }
    const button = document.getElementById("previewPlan");
    if (button) { button.disabled = true; button.textContent = "Planning…"; }
    if (output) output.textContent = "Building a safe execution plan…";
    try {
      const data = await api("/v1/runtime/plan", {
        method: "POST",
        body: JSON.stringify({goal, confirmed: false}),
      });
      const lines = data.steps.map(step => {
        const auth = data.authorization?.find(item => item.step === step.index);
        const state = auth?.allowed ? "READY" : (auth?.requires_confirmation ? "CONFIRM" : "BLOCKED");
        return `${step.index + 1}. ${step.action} · ${step.capability} · ${state}\n   ${JSON.stringify(step.payload)}`;
      });
      if (output) output.textContent = lines.join("\n") || "No safe steps generated.";
    } catch (error) {
      if (output) output.textContent = `Plan failed: ${error.message}`;
    } finally {
      if (button) { button.disabled = false; button.textContent = "Preview Plan"; }
    }
  }

  async function executePlan() {
    const goal = document.getElementById("builderGoal")?.value.trim();
    const output = document.getElementById("planPreview");
    if (!goal) {
      if (output) output.textContent = "Describe a goal first.";
      return;
    }
    const button = document.getElementById("executePlan");
    if (button) { button.disabled = true; button.textContent = "Executing…"; }
    if (output) output.textContent = "Authorizing plan and starting agent…";
    try {
      const data = await api("/v1/runtime/tasks", {
        method: "POST",
        body: JSON.stringify({goal, confirmed: true, context: {source: "agent-builder"}}),
      });
      if (output) output.textContent = `Task ${String(data.task_id || "").slice(0, 12)}\nStatus: ${data.status}\n${data.plan?.length || 0} step(s) submitted.`;
      setTimeout(() => openWorkspaceSection("console"), 250);
    } catch (error) {
      if (output) output.textContent = `Execution failed: ${error.message}`;
    } finally {
      if (button) { button.disabled = false; button.textContent = "Execute Plan"; }
    }
  }

  async function refreshConsole() {
    const output = document.getElementById("consoleOutput");
    if (!output) return;
    output.textContent = "Refreshing runtime…";
    try {
      const data = await api("/v1/runtime/state");
      const tasks = Object.entries(data.active_tasks || {});
      if (!tasks.length) {
        output.textContent = "RUNTIME ONLINE\n\nNo active tasks.\nConnected devices: " + (data.connected_devices?.length || 0);
        return;
      }
      output.textContent = tasks.map(([id, task]) => {
        const plan = task.plan || [];
        const steps = plan.length ? `\nSteps: ${task.step_status?.map((s, i) => `${i + 1}:${s}`).join(" | ")}` : "";
        return `TASK ${id.slice(0, 12)}\nStatus: ${task.status}\nGoal: ${task.goal}${steps}\nDetail: ${task.detail || ""}`;
      }).join("\n\n") + `\n\nConnected devices: ${data.connected_devices?.length || 0}`;
    } catch (error) {
      output.textContent = `Console unavailable: ${error.message}`;
    }
  }

  async function stopAgentFromConsole() {
    try {
      await api("/v1/agent/stop", {method: "POST"});
      await refreshConsole();
    } catch (error) {
      const output = document.getElementById("consoleOutput");
      if (output) output.textContent = `Emergency stop failed: ${error.message}`;
    }
  }

  async function resumeAgentFromConsole() {
    try {
      await api("/v1/agent/resume", {method: "POST"});
      await refreshConsole();
    } catch (error) {
      const output = document.getElementById("consoleOutput");
      if (output) output.textContent = `Resume failed: ${error.message}`;
    }
  }

  document.getElementById("previewPlan")?.addEventListener("click", previewPlan);
  document.getElementById("executePlan")?.addEventListener("click", executePlan);
  document.getElementById("refreshConsole")?.addEventListener("click", refreshConsole);
  document.getElementById("consoleStop")?.addEventListener("click", stopAgentFromConsole);
  document.getElementById("resumeAgent")?.addEventListener("click", resumeAgentFromConsole);
})();
