import { useState } from "react";
import { useSimulation } from "../hooks/useSimulation.jsx";

export default function ApprovalModal({ open, onClose }) {
  const { state, actions, busy } = useSimulation();
  const rec = state?.recommended_defense || {};
  const gate = state?.approval_gate || {};
  const [reason, setReason] = useState("Simulated containment approved by analyst");
  const [modified, setModified] = useState("ISOLATE_AND_REVOKE");
  if (!open) return null;

  const submit = (decision) => {
    actions
      .approve({
        action: rec.action || "ISOLATE_AND_REVOKE",
        decision,
        approver: gate.mode === "security_administrator" ? "secadmin.demo" : "analyst.demo",
        reason,
        modified_action: decision === "MODIFY" ? modified : rec.action,
      })
      .then(onClose);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="panel w-full max-w-xl p-5">
        <div className="text-lg font-semibold">Human approval required</div>
        <p className="mt-2 text-sm text-soc-muted">
          Risk gate: {gate.level || "n/a"} ({gate.mode}). No real network action will be taken.
        </p>
        <div className="mt-3 rounded-lg bg-soc-raised p-3 text-sm">
          Recommended: <b>{rec.action || "n/a"}</b>
          <div className="text-soc-muted">Synthetic environment. No real network action will be taken.</div>
        </div>
        <label className="mt-3 block text-xs text-soc-muted">Reason</label>
        <textarea className="mt-1 w-full rounded-lg border border-soc-border bg-soc-bg p-2 text-sm" rows={3} value={reason} onChange={(e) => setReason(e.target.value)} />
        <label className="mt-3 block text-xs text-soc-muted">Modify action</label>
        <select className="mt-1 w-full rounded-lg border border-soc-border bg-soc-bg p-2 text-sm" value={modified} onChange={(e) => setModified(e.target.value)}>
          {["REVOKE_CREDENTIALS", "ISOLATE_ENDPOINT", "BLOCK_NETWORK_PATH", "ISOLATE_AND_REVOKE", "EMERGENCY_SERVER_SHUTDOWN"].map((a) => (
            <option key={a}>{a}</option>
          ))}
        </select>
        <div className="mt-4 flex flex-wrap gap-2">
          <button className="btn btn-good" disabled={!!busy} onClick={() => submit("APPROVE")}>Approve</button>
          <button className="btn btn-danger" disabled={!!busy} onClick={() => submit("REJECT")}>Reject</button>
          <button className="btn btn-ghost" disabled={!!busy} onClick={() => submit("MODIFY")}>Modify</button>
          <button
            className="btn btn-ghost"
            disabled={!!busy}
            onClick={() => actions.simulateDefense({ action: rec.action || modified })}
          >
            Simulate first
          </button>
          <button className="btn btn-ghost ml-auto" onClick={onClose}>Close</button>
        </div>
        {state?.defense_preview ? (
          <div className="mt-3 text-xs text-soc-muted">
            Preview: {state.defense_preview.notes?.join(" · ")} (simulated)
          </div>
        ) : null}
      </div>
    </div>
  );
}
