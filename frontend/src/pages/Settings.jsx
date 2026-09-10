import { useEffect, useState } from "react";
import { api } from "../services/api.js";
import YamlViewer from "../components/YamlViewer.jsx";
import { useSimulation } from "../hooks/useSimulation.jsx";

export default function Settings() {
  const { actions, busy, state } = useSimulation();
  const [yaml, setYaml] = useState(null);
  const [audit, setAudit] = useState(null);
  const [assets, setAssets] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.yaml(), api.audit(), api.assets(), api.scenarios()])
      .then(([y, a, as, sc]) => {
        setYaml(y);
        setAudit(a);
        setAssets(as.assets || []);
        setScenarios(sc.scenarios || []);
      })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
      <p className="text-sm text-soc-muted">
        Product configuration. All telemetry and assets are synthetic. Gemini key is optional and never required for decisions.
      </p>
      {error ? <div className="text-soc-crit text-sm">{error}</div> : null}
      <div className="panel p-4">
        <div className="text-xs uppercase text-soc-muted">False-positive lab</div>
        <p className="mt-2 text-sm">Benign scenarios use the same detection pipeline to show contextual correlation.</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {scenarios.map((s) => (
            <button key={s.id} className="btn btn-ghost" disabled={!!busy} onClick={() => actions.start(s.id).then(() => actions.nextEvent())}>
              {s.name}
            </button>
          ))}
        </div>
        <div className="mt-3 text-sm">
          Correlation context: {state?.false_positive_context?.correlation || "n/a"}
        </div>
      </div>
      <div className="panel p-4">
        <div className="text-xs uppercase text-soc-muted">MITRE ATT&CK coverage</div>
        <div className="mt-2 flex flex-wrap gap-2">
          {(state?.mitre?.catalog || []).map((t) => {
            const hit = (state?.mitre?.observed || []).some((o) => o.id === t.id);
            return (
              <span key={t.id} className={`rounded-lg px-3 py-1 text-xs ${hit ? "bg-soc-good/20 text-soc-good" : "bg-soc-raised text-soc-muted"}`}>
                {t.id} {t.name}
              </span>
            );
          })}
        </div>
        <div className="mt-2 text-xs text-soc-muted">Coverage {state?.mitre?.coverage ?? 0}%</div>
      </div>
      <div className="panel overflow-auto">
        <div className="px-4 py-2 text-xs uppercase text-soc-muted">Synthetic assets</div>
        <table className="w-full text-left text-sm">
          <thead className="text-xs text-soc-muted">
            <tr>
              <th className="p-3">ID</th>
              <th>Name</th>
              <th>Type</th>
              <th>Criticality</th>
              <th>Segment</th>
            </tr>
          </thead>
          <tbody>
            {assets.map((a) => (
              <tr key={a.id} className="border-t border-soc-border">
                <td className="p-3">{a.id}</td>
                <td>{a.name}</td>
                <td>{a.type}</td>
                <td>{a.criticality}</td>
                <td>{a.segment}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="panel p-4">
        <div className="text-xs uppercase text-soc-muted">Audit integrity</div>
        <p className="mt-2 text-sm">
          Hash chain {audit?.integrity?.intact ? "INTACT" : "UNKNOWN"} · entries {audit?.integrity?.entries ?? 0}
        </p>
        <p className="text-xs text-soc-muted">{audit?.integrity?.label}</p>
        <div className="mt-3 max-h-64 overflow-auto text-xs">
          {(audit?.logs || []).slice(-12).map((l) => (
            <div key={l.id} className="border-t border-soc-border py-2">
              {l.timestamp} · {l.event_type} · {l.actor} · {l.hash?.slice(0, 16)}…
            </div>
          ))}
        </div>
      </div>
      <YamlViewer title="Detection rules YAML" text={yaml?.detection_rules} />
    </div>
  );
}
