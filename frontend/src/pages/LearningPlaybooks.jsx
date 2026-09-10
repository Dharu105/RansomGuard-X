import { useEffect, useState } from "react";
import { api } from "../services/api.js";
import YamlViewer from "../components/YamlViewer.jsx";
import { useSimulation } from "../hooks/useSimulation.jsx";

export default function LearningPlaybooks() {
  const { state, actions, busy } = useSimulation();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const load = () => {
    api.playbooks().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(() => {
    load();
  }, []);
  const proposal = state?.playbook || {};

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold tracking-tight">Playbook Evolution</h1>
      <p className="text-sm text-soc-muted">YAML is loaded from the backend. Updates require human acceptance.</p>
      {err ? <div className="text-soc-crit text-sm">{err}</div> : null}
      <div className="panel p-4">
        <div className="text-xs uppercase text-soc-muted">Proposed update</div>
        {proposal?.proposed || proposal?.proposal_id ? (
          <div className="mt-2 text-sm">
            <div>{proposal.change_reason || proposal.note}</div>
            <div className="mt-2 flex gap-2">
              <button className="btn btn-good" disabled={!!busy} onClick={() => actions.approvePlaybook({ proposal_id: proposal.proposal_id, decision: "ACCEPT" }).then(load)}>
                Accept update
              </button>
              <button className="btn btn-ghost" disabled={!!busy} onClick={() => actions.approvePlaybook({ proposal_id: proposal.proposal_id, decision: "REVIEW" }).then(load)}>
                Review
              </button>
              <button className="btn btn-danger" disabled={!!busy} onClick={() => actions.approvePlaybook({ proposal_id: proposal.proposal_id, decision: "REJECT" }).then(load)}>
                Reject
              </button>
            </div>
          </div>
        ) : (
          <p className="mt-2 text-sm text-soc-muted">Contain an incident to propose a playbook version. The system never silently changes controls.</p>
        )}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <YamlViewer title="Playbooks YAML (backend)" text={data?.raw_yaml || proposal.yaml_body} />
        <div className="space-y-3">
          {(data?.playbooks || []).map((pb) => (
            <div key={pb.id} className="panel p-4 text-sm">
              <div className="font-semibold">{pb.name}</div>
              <div className="text-soc-muted">v{pb.current_version} · {pb.status}</div>
              <ul className="mt-2 text-xs">
                {(pb.versions || []).map((v) => (
                  <li key={v.id}>v{v.version} {v.status} — {v.change_reason}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
      <div className="panel p-4 text-sm">
        <div className="text-xs uppercase text-soc-muted">Defense memory</div>
        {(state?.learning?.memory || []).length ? (
          <ul className="mt-2 space-y-1">
            {state.learning.memory.map((m) => (
              <li key={m.id}>{m.incident_id}: {m.defense_used} → {m.outcome} ({m.decision_quality})</li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-soc-muted">Memory fills after simulated containment.</p>
        )}
      </div>
    </div>
  );
}
