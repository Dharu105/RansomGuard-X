/** Shared simulation state shapes. Frontend never invents security values. */

export const LOOP_STAGES = [
  "DETECT",
  "UNDERSTAND",
  "PREDICT",
  "DECIDE",
  "DEFEND",
  "REPLAY",
  "COMPARE",
  "LEARN",
  "IMPROVE",
];

export const NAV = [
  { to: "/", label: "Command Center" },
  { to: "/live", label: "Live Defense" },
  { to: "/graph", label: "Attack Graph" },
  { to: "/intervention", label: "Intervention Window" },
  { to: "/counterfactual", label: "Counterfactual Replay" },
  { to: "/alternate", label: "Alternate Reality" },
  { to: "/intelligence", label: "Defense Intelligence" },
  { to: "/playbooks", label: "Learning & Playbooks" },
  { to: "/history", label: "Incident History" },
  { to: "/investigator", label: "AI Investigator" },
  { to: "/evaluation", label: "Evaluation" },
  { to: "/settings", label: "Settings" },
];
