const TOKEN_KEY = "ai-interview-token";
const USER_KEY = "ai-interview-user";
const ACTIVE_INTERVIEW_KEY = "ai-interview-active";

let timerHandle = null;

document.addEventListener("DOMContentLoaded", () => {
  configureNavigation();

  const page = document.body.dataset.page;
  if (page === "login") {
    initLoginPage();
  } else if (page === "register") {
    initRegisterPage();
  } else if (page === "dashboard") {
    initDashboardPage();
  } else if (page === "interview") {
    initInterviewPage();
  }
});

function configureNavigation() {
  const navSlot = document.getElementById("navAuthActions");
  if (!navSlot) {
    return;
  }

  const user = getStoredUser();
  if (user && getToken()) {
    navSlot.innerHTML = `
      <span class="nav-user">${escapeHtml(user.email)}</span>
      <button class="btn btn-ghost" id="logoutButton" type="button">Logout</button>
    `;
    document.getElementById("logoutButton").addEventListener("click", logout);
    return;
  }

  navSlot.innerHTML = `
    <a href="/login">Login</a>
    <a class="btn btn-ghost" href="/register">Register</a>
  `;
}

function initLoginPage() {
  const form = document.getElementById("loginForm");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const payload = {
      email: formData.get("email"),
      password: formData.get("password"),
    };

    try {
      setMessage("loginMessage", "Signing you in...", "info");
      const response = await apiRequest("/auth/login", {
        method: "POST",
        body: payload,
      });
      persistAuth(response);
      window.location.href = "/dashboard";
    } catch (error) {
      setMessage("loginMessage", error.message, "error");
    }
  });
}

function initRegisterPage() {
  const form = document.getElementById("registerForm");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const payload = {
      email: formData.get("email"),
      password: formData.get("password"),
    };

    try {
      setMessage("registerMessage", "Creating your account...", "info");
      const response = await apiRequest("/auth/register", {
        method: "POST",
        body: payload,
      });
      persistAuth(response);
      window.location.href = "/dashboard";
    } catch (error) {
      setMessage("registerMessage", error.message, "error");
    }
  });
}

async function initDashboardPage() {
  if (!requireAuth()) {
    return;
  }

  const user = getStoredUser();
  const userLabel = document.getElementById("dashboardUserLabel");
  userLabel.textContent = `Signed in as ${user.email}. Your saved interview progress appears below.`;

  try {
    const [stats, history] = await Promise.all([
      apiRequest("/dashboard/stats"),
      apiRequest("/interview/history"),
    ]);
    renderStatsCards(stats);
    renderBreakdown("roleBreakdown", stats.role_breakdown, 10, "score");
    renderBreakdown("difficultyBreakdown", stats.difficulty_breakdown, 10, "score");
    renderProgressSeries(stats.progress_series);
    renderRecentFeedback(stats.recent_feedback);
    renderHistory(history);
  } catch (error) {
    setMessage("dashboardMessage", error.message, "error");
  }
}

async function initInterviewPage() {
  if (!requireAuth()) {
    return;
  }

  const user = getStoredUser();
  document.getElementById("interviewUserLabel").textContent = `Practicing as ${user.email}. Your active draft is saved locally until submission.`;

  const startForm = document.getElementById("startInterviewForm");
  startForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const activeState = getActiveInterview();
    if (activeState && !activeState.submitted) {
      setMessage("interviewMessage", "Finish or clear the active draft before starting another interview.", "error");
      return;
    }

    const formData = new FormData(startForm);
    const payload = {
      role: formData.get("role"),
      difficulty: formData.get("difficulty"),
      num_questions: Number(formData.get("num_questions")),
    };

    try {
      setMessage("interviewMessage", "Generating your interview questions...", "info");
      const response = await apiRequest("/interview/start", {
        method: "POST",
        body: payload,
      });
      const state = {
        interviewId: response.interview_id,
        role: response.role,
        difficulty: response.difficulty,
        attemptNumber: response.attempt_number,
        questions: response.questions,
        answers: response.questions.map(() => ""),
        createdAt: response.created_at,
        startedAt: Date.now(),
        durationSeconds: response.duration_seconds,
        submitted: false,
      };
      saveActiveInterview(state);
      setMessage("interviewMessage", "Interview started. Answer each question and submit when ready.", "success");
      renderInterviewSession(state);
      document.getElementById("interviewResults").classList.add("hidden");
    } catch (error) {
      setMessage("interviewMessage", error.message, "error");
    }
  });

  document.getElementById("clearDraftButton").addEventListener("click", () => {
    clearActiveInterview();
    renderEmptyInterviewState();
    setMessage("interviewMessage", "Any active draft has been cleared.", "success");
  });

  const activeState = getActiveInterview();
  if (activeState && !activeState.submitted) {
    renderInterviewSession(activeState);
    setMessage("interviewMessage", "Restored your unfinished interview draft.", "info");
  } else {
    renderEmptyInterviewState();
  }
}

function renderStatsCards(stats) {
  const container = document.getElementById("statsCards");
  container.innerHTML = `
    ${createStatCard("Total Interviews", String(stats.total_interviews), "All attempts started")}
    ${createStatCard("Completed", String(stats.completed_interviews), "Submitted and scored")}
    ${createStatCard("Average Score", `${stats.average_score}/10`, "Across completed interviews")}
    ${createStatCard("Best Score", `${stats.best_score}/10`, "Highest average question score")}
    ${createStatCard("Completion Rate", `${stats.completion_rate}%`, "Completed vs started")}
  `;
}

function createStatCard(label, value, hint) {
  return `
    <article class="card stat-card">
      <span class="stat-label">${label}</span>
      <strong class="stat-value">${value}</strong>
      <p class="muted-text">${hint}</p>
    </article>
  `;
}

function renderBreakdown(containerId, items, maxValue) {
  const container = document.getElementById(containerId);
  if (!items.length) {
    container.innerHTML = `<p class="muted-text">Complete a few interviews to unlock this breakdown.</p>`;
    return;
  }

  container.innerHTML = items.map((item) => {
    const width = Math.max(8, Math.round((item.average_score / maxValue) * 100));
    return `
      <div class="metric-row">
        <div class="metric-copy">
          <strong>${escapeHtml(item.label)}</strong>
          <span>${item.count} attempts</span>
        </div>
        <div class="metric-bar">
          <span style="width:${width}%"></span>
        </div>
        <strong class="metric-value">${item.average_score}/10</strong>
      </div>
    `;
  }).join("");
}

function renderProgressSeries(series) {
  const container = document.getElementById("progressSeries");
  if (!series.length) {
    container.innerHTML = `<p class="muted-text">No scored interviews yet. Start one to populate your trend view.</p>`;
    return;
  }

  container.innerHTML = series.map((point) => {
    const ratio = point.max_score ? Math.round((point.score / point.max_score) * 100) : 0;
    return `
      <div class="progress-item">
        <div class="progress-copy">
          <strong>${escapeHtml(point.label)}</strong>
          <span>${escapeHtml(point.role)}</span>
        </div>
        <div class="metric-bar">
          <span style="width:${Math.max(8, ratio)}%"></span>
        </div>
        <strong class="metric-value">${point.score}/${point.max_score}</strong>
      </div>
    `;
  }).join("");
}

function renderRecentFeedback(items) {
  const container = document.getElementById("recentFeedback");
  if (!items.length) {
    container.innerHTML = `<p class="muted-text">Recent feedback will appear here after your first completed interview.</p>`;
    return;
  }

  container.innerHTML = items.map((item) => `
    <article class="stack-card">
      <div class="stack-card-head">
        <strong>${escapeHtml(item.role)}</strong>
        <span>${item.score} total</span>
      </div>
      <p>${escapeHtml(item.summary)}</p>
      <small>${escapeHtml(item.difficulty)} • ${formatDate(item.created_at)}</small>
    </article>
  `).join("");
}

function renderHistory(history) {
  const container = document.getElementById("historyList");
  if (!history.length) {
    container.innerHTML = `<p class="muted-text">No interviews saved yet. Start a session to build your history.</p>`;
    return;
  }

  container.innerHTML = history.map((item) => {
    const total = item.scores ? `${item.scores.total}/${item.scores.max_total}` : "Pending submission";
    const summary = item.feedback ? item.feedback.summary : "Interview started but not submitted yet.";
    return `
      <article class="history-card">
        <div class="history-head">
          <div>
            <strong>${escapeHtml(item.role)}</strong>
            <span>${escapeHtml(item.difficulty)} • Attempt ${item.attempt_number}</span>
          </div>
          <span class="pill ${item.status === "completed" ? "pill-success" : "pill-pending"}">${escapeHtml(item.status)}</span>
        </div>
        <p>${escapeHtml(summary)}</p>
        <div class="history-foot">
          <span>${total}</span>
          <span>${formatDate(item.created_at)}</span>
        </div>
      </article>
    `;
  }).join("");
}

function renderInterviewSession(state) {
  const container = document.getElementById("interviewSession");
  container.classList.remove("hidden");

  container.innerHTML = `
    <div class="section-heading">
      <span class="eyebrow">${escapeHtml(state.role)} • ${escapeHtml(state.difficulty)}</span>
      <h2>Attempt ${state.attemptNumber}</h2>
    </div>
    <p class="muted-text">Answer every question before submitting. Your responses are autosaved in this browser.</p>
    <form id="answerForm" class="question-stack">
      ${state.questions.map((question, index) => `
        <article class="question-card">
          <div class="question-meta">
            <span class="pill">Question ${index + 1}</span>
          </div>
          <h3>${escapeHtml(question)}</h3>
          <textarea name="answer-${index}" rows="7" placeholder="Write your answer here...">${escapeHtml(state.answers[index] || "")}</textarea>
        </article>
      `).join("")}
      <div class="button-row">
        <button class="btn btn-primary" id="submitInterviewButton" type="submit">Submit Interview</button>
        <button class="btn btn-secondary" id="saveDraftButton" type="button">Save Draft</button>
      </div>
    </form>
  `;

  const form = document.getElementById("answerForm");
  const textareas = [...form.querySelectorAll("textarea")];
  textareas.forEach((textarea, index) => {
    textarea.addEventListener("input", () => {
      const nextState = getActiveInterview();
      if (!nextState) {
        return;
      }
      nextState.answers[index] = textarea.value;
      saveActiveInterview(nextState);
    });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await submitInterview();
  });

  document.getElementById("saveDraftButton").addEventListener("click", () => {
    const nextState = getActiveInterview();
    if (!nextState) {
      return;
    }
    textareas.forEach((textarea, index) => {
      nextState.answers[index] = textarea.value;
    });
    saveActiveInterview(nextState);
    setMessage("interviewMessage", "Draft saved locally.", "success");
  });

  syncAnswersFromDOM();
  startTimer(state);
}

function renderEmptyInterviewState() {
  clearTimer();
  document.getElementById("timerDisplay").textContent = "00:00";
  const session = document.getElementById("interviewSession");
  session.classList.add("hidden");
  session.innerHTML = "";
  const results = document.getElementById("interviewResults");
  results.classList.add("hidden");
  results.innerHTML = "";
}

function renderInterviewResults(result) {
  const results = document.getElementById("interviewResults");
  results.classList.remove("hidden");

  const breakdown = result.feedback.breakdown || [];
  results.innerHTML = `
    <div class="section-heading">
      <span class="eyebrow">Interview review completed</span>
      <h2>${result.role} • ${result.difficulty}</h2>
    </div>
    <div class="stats-grid compact-grid">
      ${createStatCard("Total Score", `${result.scores.total}/${result.scores.max_total}`, "Combined across all questions")}
      ${createStatCard("Average", `${result.scores.average}/10`, "Average per question")}
      ${createStatCard("Questions", String(breakdown.length), "Questions evaluated")}
    </div>
    <article class="result-summary">
      <p>${escapeHtml(result.feedback.summary)}</p>
      <div class="triple-grid">
        <div>
          <h3>Strengths</h3>
          <ul class="feature-list">
            ${result.feedback.strengths.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
          </ul>
        </div>
        <div>
          <h3>Weaknesses</h3>
          <ul class="feature-list">
            ${result.feedback.weaknesses.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
          </ul>
        </div>
        <div>
          <h3>Suggestions</h3>
          <ul class="feature-list">
            ${result.feedback.suggestions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
          </ul>
        </div>
      </div>
    </article>
    <div class="question-stack">
      ${breakdown.map((item, index) => `
        <article class="question-card result-card">
          <div class="history-head">
            <strong>Question ${index + 1}</strong>
            <span class="pill pill-success">${item.score}/10</span>
          </div>
          <h3>${escapeHtml(item.question)}</h3>
          <p class="answer-preview">${escapeHtml(item.answer || "No answer submitted.")}</p>
          <div class="triple-grid">
            <div>
              <h4>Strengths</h4>
              <ul class="feature-list">${item.strengths.map((entry) => `<li>${escapeHtml(entry)}</li>`).join("")}</ul>
            </div>
            <div>
              <h4>Weaknesses</h4>
              <ul class="feature-list">${item.weaknesses.map((entry) => `<li>${escapeHtml(entry)}</li>`).join("")}</ul>
            </div>
            <div>
              <h4>Suggestions</h4>
              <ul class="feature-list">${item.suggestions.map((entry) => `<li>${escapeHtml(entry)}</li>`).join("")}</ul>
            </div>
          </div>
        </article>
      `).join("")}
    </div>
  `;
}

async function submitInterview() {
  const state = getActiveInterview();
  if (!state) {
    setMessage("interviewMessage", "No active interview was found.", "error");
    return;
  }

  syncAnswersFromDOM();
  const refreshedState = getActiveInterview();
  const submitButton = document.getElementById("submitInterviewButton");
  submitButton.disabled = true;

  try {
    setMessage("interviewMessage", "Submitting answers for evaluation...", "info");
    const result = await apiRequest("/interview/submit", {
      method: "POST",
      body: {
        interview_id: refreshedState.interviewId,
        answers: refreshedState.answers,
      },
    });
    clearTimer();
    clearActiveInterview();
    document.getElementById("interviewSession").classList.add("hidden");
    renderInterviewResults(result);
    setMessage("interviewMessage", "Evaluation complete. Review your feedback below.", "success");
  } catch (error) {
    submitButton.disabled = false;
    setMessage("interviewMessage", error.message, "error");
  }
}

function startTimer(state) {
  clearTimer();
  updateTimerDisplay(state);
  timerHandle = window.setInterval(() => {
    const activeState = getActiveInterview();
    if (!activeState) {
      clearTimer();
      return;
    }
    const remainingSeconds = getRemainingSeconds(activeState);
    updateTimerDisplay(activeState);
    if (remainingSeconds <= 0) {
      clearTimer();
      setMessage("interviewMessage", "Time is up. Submitting your answers automatically.", "info");
      submitInterview();
    }
  }, 1000);
}

function updateTimerDisplay(state) {
  const remainingSeconds = Math.max(0, getRemainingSeconds(state));
  const minutes = String(Math.floor(remainingSeconds / 60)).padStart(2, "0");
  const seconds = String(remainingSeconds % 60).padStart(2, "0");
  document.getElementById("timerDisplay").textContent = `${minutes}:${seconds}`;
}

function getRemainingSeconds(state) {
  const elapsedSeconds = Math.floor((Date.now() - state.startedAt) / 1000);
  return state.durationSeconds - elapsedSeconds;
}

function clearTimer() {
  if (timerHandle) {
    window.clearInterval(timerHandle);
    timerHandle = null;
  }
}

function syncAnswersFromDOM() {
  const state = getActiveInterview();
  const session = document.getElementById("interviewSession");
  if (!state || !session || session.classList.contains("hidden")) {
    return;
  }
  const textareas = [...session.querySelectorAll("textarea")];
  state.answers = textareas.map((textarea) => textarea.value);
  saveActiveInterview(state);
}

function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");

  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(path, {
    method: options.method || "GET",
    headers,
    body: options.body && !(options.body instanceof FormData) ? JSON.stringify(options.body) : options.body,
  }).then(async (response) => {
    const rawText = await response.text();
    let data = {};
    try {
      data = rawText ? JSON.parse(rawText) : {};
    } catch {
      data = { detail: rawText || "Request failed." };
    }

    if (!response.ok) {
      if (response.status === 401) {
        logout(false);
        if (document.body.dataset.page === "dashboard" || document.body.dataset.page === "interview") {
          window.location.href = "/login";
        }
      }
      throw new Error(data.detail || "Request failed.");
    }
    return data;
  });
}

function persistAuth(payload) {
  localStorage.setItem(TOKEN_KEY, payload.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function getStoredUser() {
  const rawUser = localStorage.getItem(USER_KEY);
  return rawUser ? JSON.parse(rawUser) : null;
}

function requireAuth() {
  if (!getToken() || !getStoredUser()) {
    window.location.href = "/login";
    return false;
  }
  return true;
}

function saveActiveInterview(state) {
  localStorage.setItem(ACTIVE_INTERVIEW_KEY, JSON.stringify(state));
}

function getActiveInterview() {
  const rawState = localStorage.getItem(ACTIVE_INTERVIEW_KEY);
  return rawState ? JSON.parse(rawState) : null;
}

function clearActiveInterview() {
  localStorage.removeItem(ACTIVE_INTERVIEW_KEY);
}

function logout(redirect = true) {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  clearActiveInterview();
  if (redirect) {
    window.location.href = "/login";
  }
}

function setMessage(elementId, message, type) {
  const element = document.getElementById(elementId);
  if (!element) {
    return;
  }
  element.textContent = message;
  element.className = `status-message ${type || ""}`;
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
