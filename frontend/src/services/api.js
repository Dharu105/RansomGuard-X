function apiRoot() {
  const raw = import.meta.env.VITE_API_BASE_URL;
  if (!raw) return "/api";
  return `${String(raw).replace(/\/$/, "")}/api`;
}

const API = apiRoot();

async function request(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  state: () => request("/simulation/state"),
  start: (scenario_id = "SCN-001") =>
    request("/simulation/start", { method: "POST", body: JSON.stringify({ scenario_id }) }),
  nextEvent: () => request("/simulation/next-event", { method: "POST" }),
  reset: () => request("/simulation/reset", { method: "POST" }),
  scenarios: () => request("/simulation/scenarios"),
  incidents: () => request("/incidents"),
  incident: (id) => request(`/incidents/${id}`),
  events: () => request("/events"),
  assets: () => request("/assets"),
  detectionCurrent: () => request("/detection/current"),
  graph: () => request("/attack-graph"),
  predictions: () => request("/predictions"),
  defenseRecommend: () => request("/defense/recommend"),
  recommend: () => request("/defense/recommend", { method: "POST" }),
  reviewDefense: (action) =>
    request("/defense/review", { method: "POST", body: JSON.stringify({ action: action || null }) }),
  approveDefense: (payload) => request("/defense/approve", { method: "POST", body: JSON.stringify(payload) }),
  rejectDefense: (payload) => request("/defense/reject", { method: "POST", body: JSON.stringify(payload) }),
  defenseStatus: () => request("/defense/status"),
  forks: () => request("/forks"),
  adaptation: () => request("/adaptation"),
  learningSummary: () => request("/learning/summary"),
  learningHistory: () => request("/learning/history"),
  approve: (payload) => request("/defense/approve", { method: "POST", body: JSON.stringify(payload) }),
  simulateDefense: (payload) =>
    request("/defense/simulate", { method: "POST", body: JSON.stringify(payload) }),
  replay: (payload) => request("/replay", { method: "POST", body: JSON.stringify(payload) }),
  counterfactual: (payload) =>
    request("/counterfactual/run", { method: "POST", body: JSON.stringify(payload) }),
  robustness: (payload) => request("/robustness/test", { method: "POST", body: JSON.stringify(payload) }),
  dropEvent: (event_type) =>
    request("/robustness/drop-event", { method: "POST", body: JSON.stringify({ event_type }) }),
  intervention: (index) => request("/intervention", { method: "POST", body: JSON.stringify({ index }) }),
  playbooks: () => request("/playbooks"),
  playbooksCurrent: () => request("/playbooks/current"),
  playbookProposals: () => request("/playbooks/proposals"),
  playbookDetail: (id) => request(`/playbooks/${id}`),
  approvePlaybookChange: (payload) =>
    request(`/playbooks/proposals/${payload.change_id}/approve`, {
      method: "POST",
      body: JSON.stringify({ actor: payload.actor || "Security Analyst", reason: payload.reason || "" }),
    }),
  rejectPlaybookChange: (payload) =>
    request(`/playbooks/proposals/${payload.change_id}/reject`, {
      method: "POST",
      body: JSON.stringify({
        actor: payload.actor || "Security Analyst",
        reason: payload.reason || "",
      }),
    }),
  yaml: () => request("/playbooks/yaml"),
  proposePlaybook: () => request("/playbook/propose", { method: "POST" }),
  approvePlaybook: (payload) =>
    request("/playbook/approve", { method: "POST", body: JSON.stringify(payload) }),
  investigate: (question) =>
    request("/ai/investigate", { method: "POST", body: JSON.stringify({ question }) }),
  investigator: () => request("/investigator"),
  investigatorStory: () => request("/investigator/story"),
  investigatorEvidence: () => request("/investigator/evidence"),
  evaluation: () => request("/evaluation"),
  evaluationScenarios: () => request("/evaluation/scenarios"),
  evaluationReport: () => request("/evaluation/report"),
  runEvaluation: (scenario_id) =>
    request("/evaluation/run", {
      method: "POST",
      body: JSON.stringify(scenario_id ? { scenario_id } : {}),
    }),
  resetEvaluation: () => request("/evaluation/reset", { method: "POST" }),
  memory: () => request("/memory"),
  audit: () => request("/audit"),
  historyMetrics: () => request("/history/metrics"),
  demo: (command) => request("/demo", { method: "POST", body: JSON.stringify({ command }) }),
};

export function wsUrl() {
  const fromEnv = import.meta.env.VITE_WS_URL;
  if (fromEnv) return String(fromEnv);
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}/ws/events`;
}
