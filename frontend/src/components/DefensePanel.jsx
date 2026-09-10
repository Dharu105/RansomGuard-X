import { useEffect, useState } from "react";
import { fmt } from "../utils/format.js";
import { EmptyState, MetaBadge } from "./ui.jsx";

export default function DefensePanel({
  defense,
  pendingApproval,
  approvalStatus,
  containmentStatus,
  selectedAction,
  approvedBy,
  verifyReason,
  busy,
  onReview,
  onApprove,
  onReject,
}) {
  const d = defense || {};
  const options = d.options || [];
  const has = Boolean(d.recommended_action);
  const [picked, setPicked] = useState(d.recommended_action || "");
  const [modal, setModal] = useState(false);
  const [rejectReason, setRejectReason] = useState("Operational disruption too high");
  const [phase, setPhase] = useState("");

  useEffect(() => {
    if (d.recommended_action && !picked) setPicked(d.recommended_action);
  }, [d.recommended_action, picked]);

  useEffect(() => {
    if (!has) {
      setModal(false);
      setPhase("");
    }
  }, [has]);

  useEffect(() => {
    if (approvalStatus === "PENDING_REVIEW") setPhase("pending");
    if (approvalStatus === "APPROVED" && containmentStatus === "SIMULATED") setPhase("running");
    if (containmentStatus === "VERIFIED") setPhase("verified");
    if (containmentStatus === "FAILED") setPhase("failed");
    if (approvalStatus === "REJECTED") setPhase("rejected");
    if (approvalStatus === "NONE") setPhase("");
  }, [approvalStatus, containmentStatus]);

  const opt = options.find((o) => o.action === (picked || d.recommended_action)) || options[0];

  const review = async () => {
    if (onReview) await onReview(picked || d.recommended_action);
    setModal(true);
    setPhase("pending");
  };

  const approve = async () => {
    setPhase("running");
    if (onApprove) await onApprove(picked || selectedAction || d.recommended_action);
    setModal(false);
  };

  const reject = async () => {
    if (onReject) await onReject(picked || selectedAction || d.recommended_action, rejectReason);
    setModal(false);
  };

  return (
    <div className="panel p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-soc-muted">Defense decision</div>
        <MetaBadge tone="amber">Human approval required</MetaBadge>
      </div>
      <p className="mt-1 text-[11px] text-soc-muted">{d.label || "SIMULATED defense projection — no real containment"}</p>

      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <div className="rounded-lg bg-soc-raised p-3">
          <div className="text-[10px] uppercase text-soc-muted">Current node</div>
          <div className="font-mono text-lg font-semibold">{d.current_node || "none"}</div>
        </div>
        <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 p-3">
          <div className="text-[10px] uppercase text-soc-muted">Predicted target</div>
          <div className="font-mono text-lg font-semibold">{d.predicted_target || "none"}</div>
        </div>
      </div>

      {phase === "pending" && (
        <div className="mt-3 rounded-lg border border-soc-warn/40 bg-soc-warn/10 p-3 text-sm">Pending human approval — no containment applied.</div>
      )}
      {phase === "running" && (
        <div className="mt-3 rounded-lg border border-cyan-500/40 p-3 text-sm">Action approved. Simulated containment running…</div>
      )}
      {phase === "verified" && (
        <div className="mt-3 animate-event-in rounded-lg border border-soc-good/50 bg-soc-good/10 p-3 text-sm">
          Action approved. Containment verified (simulated).
          {approvedBy ? ` Approved by ${approvedBy}.` : ""}
          {verifyReason ? ` ${verifyReason}` : ""}
        </div>
      )}
      {phase === "failed" && (
        <div className="mt-3 rounded-lg border border-soc-crit/40 p-3 text-sm">Containment failed: {verifyReason}</div>
      )}
      {phase === "rejected" && (
        <div className="mt-3 rounded-lg border border-soc-border p-3 text-sm">
          Action rejected. No containment occurred.
          {pendingApproval?.reason ? ` Reason: ${pendingApproval.reason}` : ""}
        </div>
      )}

      {has ? (
        <>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-[10px] uppercase text-soc-muted">
                <tr>
                  <th className="py-2">Metric</th>
                  {options.map((o) => (
                    <th key={`h-${o.action}`} className={o.action === d.recommended_action ? "text-soc-good" : ""}>
                      {o.action === d.recommended_action ? "Recommended" : o.title}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr className="border-t border-soc-border">
                  <td className="py-2 text-soc-muted">Risk after</td>
                  {options.map((o) => <td key={`r-${o.action}`} className="font-mono">{fmt(o.risk_after)}</td>)}
                </tr>
                <tr className="border-t border-soc-border">
                  <td className="py-2 text-soc-muted">Blast radius</td>
                  {options.map((o) => <td key={`b-${o.action}`}>{o.blast_radius_after}</td>)}
                </tr>
                <tr className="border-t border-soc-border">
                  <td className="py-2 text-soc-muted">Disruption</td>
                  {options.map((o) => <td key={`d-${o.action}`}>{o.operational_disruption}</td>)}
                </tr>
                <tr className="border-t border-soc-border">
                  <td className="py-2 text-soc-muted">Reversibility</td>
                  {options.map((o) => <td key={`v-${o.action}`}>{o.reversibility}</td>)}
                </tr>
              </tbody>
            </table>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {options.map((o, idx) => {
              const rec = o.action === d.recommended_action;
              return (
                <button
                  type="button"
                  key={o.action}
                  onClick={() => setPicked(o.action)}
                  className={`rounded-lg border p-3 text-left transition duration-200 hover:-translate-y-0.5 ${
                    rec ? "border-soc-good/50 bg-soc-good/5" : o.action === picked ? "border-cyan-500/40" : "border-soc-border hover:bg-soc-raised"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-[10px] uppercase text-soc-muted">{rec ? "Recommended" : `Option ${idx + 1}`}</div>
                    <div className="font-mono text-sm">Score {fmt(o.defense_score)}</div>
                  </div>
                  <div className="mt-1 font-semibold">{o.title}</div>
                  <div className="font-mono text-[11px] text-soc-muted">{o.action}</div>
                  <div className="mt-2 grid grid-cols-2 gap-1 text-xs">
                    <div>Risk before {fmt(o.risk_before)}</div>
                    <div>Risk after {fmt(o.risk_after)}</div>
                    <div>Reduction {fmt(o.risk_reduction)}</div>
                    <div>Blast-radius {o.blast_radius_before} → {o.blast_radius_after}</div>
                    <div>Disruption {o.operational_disruption}</div>
                    <div>Reversible {o.reversibility}</div>
                  </div>
                </button>
              );
            })}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button className="btn btn-ghost" disabled={!!busy} onClick={review}>Review</button>
            <button className="btn btn-good" disabled={!!busy} onClick={review}>Approve</button>
            <button className="btn btn-danger" disabled={!!busy} onClick={() => { setModal(true); }}>Reject</button>
          </div>
        </>
      ) : (
        <div className="mt-3">
          <EmptyState title="No defense recommendation" body="No defense recommendation until synthetic events produce a meaningful threat." />
        </div>
      )}

      {modal && opt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="panel w-full max-w-lg p-5" role="dialog" aria-labelledby="approval-title">
            <div id="approval-title" className="text-lg font-semibold">Human approval required</div>
            <p className="mt-1 text-xs text-soc-muted">Pending human approval. Review does not execute containment.</p>
            <div className="mt-3 rounded-lg bg-soc-raised p-3 text-sm">
              <div>Selected action: <b className="font-mono">{opt.action}</b></div>
              <div>Projected risk: {fmt(opt.risk_before)} → {fmt(opt.risk_after)}</div>
              <div>Blast: {opt.blast_radius_before} → {opt.blast_radius_after}</div>
              <div>Disruption: {opt.operational_disruption}</div>
              <p className="mt-2 text-soc-muted">{opt.reason}</p>
            </div>
            <label className="mt-3 block text-xs text-soc-muted" htmlFor="reject-reason">Reject reason</label>
            <textarea
              id="reject-reason"
              className="mt-1 w-full rounded-lg border border-soc-border bg-soc-bg p-2 text-sm"
              rows={2}
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
            />
            <div className="mt-4 flex flex-wrap gap-2">
              <button className="btn btn-good" disabled={!!busy} onClick={approve}>Approve</button>
              <button className="btn btn-danger" disabled={!!busy} onClick={reject}>Reject</button>
              <button className="btn btn-ghost ml-auto" onClick={() => setModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
