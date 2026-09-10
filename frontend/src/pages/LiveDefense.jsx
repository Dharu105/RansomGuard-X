import { useState } from "react";
import { useSimulation } from "../hooks/useSimulation.jsx";
import ApprovalModal from "../components/ApprovalModal.jsx";
import { fmt } from "../utils/format.js";

export default function LiveDefense() {
  const { state, actions, busy } = useSimulation();
  const [open, setOpen] = useState(false);
  if (!state) return <div className="text-soc-muted">Loading live defense…</div>;
  const options = state.defense_options || [];

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold tracking-tight">Live Defense</h1>
      <p className="text-sm text-soc-muted">Same incident state as Command Center. All actions are simulated.</p>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="panel p-4">
          <div className="mb-3 text-xs uppercase text-soc-muted">Live event feed</div>
          <div className="space-y-2">
            {(state.events || []).length === 0 ? <div className="text-sm text-soc-muted">Waiting for telemetry. Use Next event.</div> : null}
            {(state.events || []).map((e) => (
              <div key={e.id} className="rounded-lg border border-soc-border bg-soc-raised p-3">
                <div className="flex justify-between text-sm">
                  <b>{e.event_type}</b>
                  <span>{e.timestamp}</span>
                </div>
                <div className="text-xs text-soc-muted">{e.summary}</div>
                <div className="mt-1 text-[11px] text-soc-muted">{e.asset_id} · {e.user} · {e.mitre}</div>
              </div>
            ))}
          </div>
          <div className="mt-3 flex gap-2">
            <button className="btn btn-primary" disabled={!!busy} onClick={() => actions.nextEvent()}>Ingest next event</button>
            <button className="btn btn-ghost" disabled={!!busy} onClick={() => actions.start("SCN-001")}>Restart path</button>
          </div>
        </div>
        <div className="panel p-4">
          <div className="mb-3 text-xs uppercase text-soc-muted">Defense options (estimated)</div>
          <table className="w-full text-left text-xs">
            <thead className="text-soc-muted">
              <tr>
                <th className="py-1">Action</th>
                <th>Contain</th>
                <th>Downtime</th>
                <th>Impact</th>
                <th>Residual</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {options.map((o) => (
                <tr key={o.action} className={o.action === state.recommended_defense?.action ? "bg-soc-accent/10" : ""}>
                  <td className="py-2 font-medium">{o.action}</td>
                  <td>{o.containment}</td>
                  <td>{o.downtime}</td>
                  <td>{o.business_impact}</td>
                  <td>{o.residual_risk}</td>
                  <td>{fmt(o.overall_defense_score)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-sm">{state.recommended_defense ? `Why: isolation + revoke maximizes containment of LAB-PC-21 without emergency server shutdown.` : "Advance events to score defenses."}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button className="btn btn-ghost" disabled={!!busy} onClick={() => actions.recommend()}>Recalculate</button>
            <button className="btn btn-primary" onClick={() => setOpen(true)}>Approve / reject</button>
            <button
              className="btn btn-ghost"
              disabled={!!busy || !state.recommended_defense}
              onClick={() => actions.simulateDefense({ action: state.recommended_defense.action })}
            >
              Simulate first
            </button>
          </div>
          {state.containment ? (
            <div className="mt-3 rounded-lg bg-soc-raised p-3 text-xs">
              <div className="font-semibold">Simulated containment</div>
              {(state.containment.notes || []).map((n) => <div key={n}>{n}</div>)}
              <div className="mt-1 text-soc-muted">real_network_action = false</div>
            </div>
          ) : null}
          {state.approval ? (
            <div className="mt-2 text-xs text-soc-muted">
              Decision {state.approval.decision} by {state.approval.approver}: {state.approval.reason}
            </div>
          ) : null}
        </div>
      </div>
      <ApprovalModal open={open} onClose={() => setOpen(false)} />
    </div>
  );
}
