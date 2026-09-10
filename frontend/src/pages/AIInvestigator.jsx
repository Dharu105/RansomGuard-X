import { useState } from "react";
import { useSimulation } from "../hooks/useSimulation.jsx";
import { sanitizeBrand } from "../utils/format.js";
import AIInvestigatorPanel from "../components/AIInvestigatorPanel.jsx";
import { MetaBadge, PageHeader } from "../components/ui.jsx";

const PRESETS = [
  "Why was this classified as ransomware?",
  "What is likely to be targeted next?",
  "Why was isolation recommended?",
  "What happens if credentials are revoked earlier?",
  "What was the biggest missed intervention?",
  "Why is this defense robust?",
  "Generate incident report",
];

export default function AIInvestigator() {
  const { actions, state } = useSimulation();
  const [q, setQ] = useState(PRESETS[0]);
  const [msgs, setMsgs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const ask = async (question) => {
    setLoading(true);
    setError("");
    try {
      const res = await actions.investigate(question);
      setMsgs((m) => [...m, { q: question, ...res }]);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="AI Investigator"
        subtitle={`Analyst briefing grounded in incident ${state?.incident_id || "n/a"}. The model never invents telemetry.`}
        badges={<MetaBadge tone="purple">Simulation / experimental</MetaBadge>}
      />
      <AIInvestigatorPanel investigator={state?.investigator} />
      <div className="panel p-4">
        <div className="text-[10px] uppercase tracking-wide text-soc-muted">Directed questions</div>
        <div className="mt-3 flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <button key={p} className="btn btn-ghost text-xs" onClick={() => { setQ(p); ask(p); }}>
              {p}
            </button>
          ))}
        </div>
        <div className="mt-3 flex gap-2">
          <input
            className="flex-1 rounded-lg border border-soc-border bg-soc-bg px-3 py-2 text-sm"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            aria-label="Investigation question"
          />
          <button className="btn btn-primary" disabled={loading} onClick={() => ask(q)}>
            {loading ? "Investigating…" : "Ask"}
          </button>
        </div>
        {error ? <div className="mt-2 text-sm text-soc-crit">{error}</div> : null}
        <div className="mt-3 space-y-3">
          {msgs.map((m, i) => (
            <div key={i} className="rounded-lg border border-soc-border bg-soc-raised p-4 text-sm">
              <div className="text-soc-muted">{m.q}</div>
              <p className="mt-2 whitespace-pre-wrap">{sanitizeBrand(m.answer)}</p>
              <div className="mt-2 text-xs text-soc-muted">Source: {m.source} · invented_telemetry: {String(m.invented_telemetry)}</div>
              <ul className="mt-2 text-xs text-soc-muted">
                {(m.evidence || []).map((e) => <li key={e}>{sanitizeBrand(e)}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
