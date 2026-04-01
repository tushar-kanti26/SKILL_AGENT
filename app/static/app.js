const state = {
  learnerName: "",
  learnerId: null,
  planId: null,
  profile: null,
};

const chatBox = document.getElementById("chatBox");
const profileView = document.getElementById("profileView");
const planView = document.getElementById("planView");
const progressView = document.getElementById("progressView");
const tasksView = document.getElementById("tasksView");

function addMessage(role, content) {
  const div = document.createElement("div");
  div.className = `msg ${role === "user" ? "user" : "bot"}`;
  div.textContent = content;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function api(path, method = "GET", body = null) {
  const res = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : null,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

function renderProfile() {
  if (!state.profile) {
    profileView.textContent = "Profile will appear as chat captures details.";
    return;
  }
  profileView.innerHTML = `
    <strong>Profile</strong><br>
    Skill: ${state.profile.target_skill || "-"}<br>
    Level: ${state.profile.current_level || "-"}<br>
    Hours/week: ${state.profile.weekly_hours || "-"}<br>
    Weeks: ${state.profile.timeline_weeks || "-"}<br>
    Goal: ${state.profile.goal || "-"}
  `;
}

async function sendChat() {
  if (!state.learnerName) {
    alert("Set your name first.");
    return;
  }
  const input = document.getElementById("messageInput");
  const message = input.value.trim();
  if (!message) return;

  addMessage("user", message);
  input.value = "";

  try {
    const data = await api("/api/chat", "POST", {
      learner_name: state.learnerName,
      message,
    });

    state.learnerId = data.learner_id;
    state.profile = data.collected_profile;
    renderProfile();

    addMessage("bot", data.assistant_message);
    if (data.ready_for_plan) {
      addMessage("bot", "You can now click Generate Plan.");
    }
  } catch (err) {
    addMessage("bot", `Error: ${err.message}`);
  }
}

async function generatePlan() {
  if (!state.learnerId) {
    alert("Complete profile chat first.");
    return;
  }

  try {
    const plan = await api("/api/plans", "POST", { learner_id: state.learnerId });
    state.planId = plan.plan_id;

    planView.innerHTML = `
      <strong>Plan</strong><br>
      Skill: ${plan.skill_name}<br>
      Level: ${plan.level}<br>
      Timeline: ${plan.timeline_weeks} weeks<br>
      Hours/week: ${plan.hours_per_week}
    `;

    await loadTasks();
    await loadProgress();
  } catch (err) {
    alert(err.message);
  }
}

async function setTaskProgress(taskId, completed) {
  await api(`/api/tasks/${taskId}/progress`, "PATCH", { completed });
  await loadProgress();
}

async function loadTasks() {
  if (!state.planId) return;
  const tasks = await api(`/api/plans/${state.planId}/tasks`);

  tasksView.innerHTML = "";
  tasks.forEach((task) => {
    const div = document.createElement("div");
    div.className = "task";
    div.innerHTML = `
      <div class="task-title">W${task.week_number} ${task.day_label} - ${task.title}</div>
      <div class="task-meta">${task.resource_type} | ${task.estimated_minutes} min</div>
      <div><a href="${task.resource_url}" target="_blank" rel="noreferrer">${task.resource_title}</a></div>
      <label><input type="checkbox" ${task.completed ? "checked" : ""}/> Completed</label>
    `;

    const checkbox = div.querySelector("input[type='checkbox']");
    checkbox.addEventListener("change", async (e) => {
      await setTaskProgress(task.task_id, e.target.checked);
    });

    tasksView.appendChild(div);
  });
}

async function loadProgress() {
  if (!state.learnerId || !state.planId) return;
  const p = await api(`/api/learners/${state.learnerId}/plans/${state.planId}/progress`);
  progressView.innerHTML = `
    <strong>Progress</strong><br>
    Completed: ${p.completed_tasks}/${p.total_tasks}<br>
    Rate: ${p.completion_rate}%
  `;
}

document.getElementById("setNameBtn").addEventListener("click", () => {
  const v = document.getElementById("nameInput").value.trim();
  if (!v) return;
  state.learnerName = v;
  addMessage("bot", `Welcome ${v}. Tell me what skill you want to learn.`);
});

document.getElementById("sendBtn").addEventListener("click", sendChat);
document.getElementById("messageInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendChat();
});
document.getElementById("generatePlanBtn").addEventListener("click", generatePlan);

renderProfile();
planView.textContent = "Plan details will appear after generation.";
progressView.textContent = "Progress summary will appear after plan generation.";
