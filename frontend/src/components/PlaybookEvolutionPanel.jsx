import { useState } from "react";
import { EmptyState, MetaBadge } from "./ui.jsx";

export default function PlaybookEvolutionPanel({ evolution, busy, onApprove, onReject }) {
  const evo = evolution || {};
  const current = evo.current || {};
  const versions = evo.versions || [];
  const open = evo.open_proposal;
  const diff = evo.diff || {};
  const [review, setReview] = useState(false);

  const label = current.label || (current.playbook_id ? `${current.playbook_id}_V${current.version}` : "—");
  const added = diff.added || [];
  const removed = diff.removed || [];
  const unchanged = (diff.unchanged || []).map((s) => s.title || s.id);
  const evidence = open?.supporting_evidence || [];
  const versionList = versions.length ? versions : current.version ? [{ version: current.version, status: current.status }] : [];

  return (
    <div className="panel p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-soc-muted">Playbook evolution</div>
        <MetaBadge tone="amber">Human approval required</MetaBadge>
      </div>
      <p className="mt-1 text-sm text-soc-muted">
        The system proposes evidence-backed playbook improvements for human approval.
      </p>
      <p className="text-[11px] text-soc-muted">
        Synthetic workflow description only. No real security action is executed. YAML is not executed as code.
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-2 font-mono text-sm">
        {versionList.map((v, i) => (
          <span key={v.version} className="flex items-center gap-2">
            <span className={`rounded border px-2 py-0.5 ${v.status === "ACTIVE" || v.version === current.version ? "border-soc-good/40 text-soc-good" : "border-soc-border text-soc-muted"}`}>
              V{v.version}{v.status === "ACTIVE" || v.version === current.version ? " ACTIVE" : ""}
            </span>
            {i < versionList.length - 1 || open ? <span className="text-soc-muted">→</span> : null}
          </span>
        ))}
        {open ? (
          <span className="rounded border border-violet-500/40 px-2 py-0.5 text-violet-400">V{open.proposed_version} PROPOSED</span>
        ) : null}
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <div className="rounded-lg bg-soc-raised p-3">
          <div className="text-[10px] uppercase text-soc-muted">Current playbook</div>
          <div className="text-lg font-semibold">{label}</div>
          <div className="text-sm">Status: {current.status || "ACTIVE"}</div>
          <div className="text-xs text-soc-muted">Trigger: {current.trigger || "ransomware_likely"}</div>
        </div>
        <div className="rounded-lg bg-soc-raised p-3">
          <div className="text-[10px] uppercase text-soc-muted">Governance</div>
          <div className="text-sm">DETECT → ANALYZE → PROPOSE</div>
          <div className="text-sm">No auto-approve, auto-publish, or auto-execute.</div>
        </div>
      </div>

      {open ? (
        <div className="mt-4 rounded-lg border border-soc-border p-3">
          <div className="text-[10px] uppercase text-soc-muted">Proposed evolution</div>
          <div className="text-lg font-semibold">
            V{open.current_version} → V{open.proposed_version}
          </div>
          <p className="mt-2 text-sm">{open.reason}</p>
          <div className="mt-2 text-[10px] uppercase text-soc-muted">Supporting evidence</div>
          <ul className="mt-1 space-y-1 text-sm">
            {evidence.map((item) => (
              <li key={item}>● {item}</li>
            ))}
          </ul>
          <div className="mt-3 grid gap-2 text-sm md:grid-cols-3">
            <div>Expected benefit: {open.expected_benefit || "improved synthetic response"}</div>
            <div>Risk: {open.risk || "requires human review"}</div>
            <div>Status: {open.status} · {open.change_type}</div>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <button className="btn btn-ghost" type="button" onClick={() => setReview((v) => !v)}>Review change</button>
            <button className="btn btn-good" type="button" disabled={!!busy} onClick={() => onApprove(open.change_id)}>Approve</button>
            <button className="btn btn-danger" type="button" disabled={!!busy} onClick={() => onReject(open.change_id)}>Reject</button>
          </div>
        </div>
      ) : (
        <div className="mt-4">
          <EmptyState title="No proposed evolution" body="Proposals appear only when historical synthetic evidence is sufficient." />
        </div>
      )}

      {review && open && (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {versions.map((v) => (
            <div key={v.version} className="rounded-lg border border-soc-border p-3">
              <div className="text-[10px] uppercase text-soc-muted">
                Version {v.version} {v.status === "ACTIVE" ? "(active)" : ""}
              </div>
              <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">
                {(v.steps || []).map((s) => (
                  <li key={`${v.version}-${s.id}`}>{s.title || s.id}</li>
                ))}
              </ol>
            </div>
          ))}
          {open.proposed_steps && (
            <div className="rounded-lg border border-soc-border p-3 md:col-span-2">
              <div className="text-[10px] uppercase text-soc-muted">Proposed V{open.proposed_version}</div>
              <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">
                {open.proposed_steps.map((s) => (
                  <li key={`p-${s.id}`}>{s.title || s.id}</li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}

      {open && (
        <div className="mt-4 rounded-lg bg-soc-raised p-3 font-mono text-sm">
          <div className="text-[10px] uppercase tracking-wide text-soc-muted">
            Diff · V{open.current_version} → V{open.proposed_version}
          </div>
          <div className="mt-2 text-soc-good">
            <div className="text-[10px] uppercase">Added</div>
            {added.length ? added.map((s) => <div key={s.id}>+ {s.title || s.id}</div>) : <div>—</div>}
          </div>
          <div className="mt-2 text-soc-crit">
            <div className="text-[10px] uppercase">Removed</div>
            {removed.length ? removed.map((s) => <div key={s.id}>- {s.title || s.id}</div>) : <div>—</div>}
          </div>
          <div className="mt-2 text-soc-warn">
            <div className="text-[10px] uppercase">Reordered</div>
            <div>{diff.reordered ? "Prediction / defense comparison order changed" : "No reorder"}</div>
          </div>
          <div className="mt-2 text-soc-muted">
            <div className="text-[10px] uppercase">Unchanged</div>
            <div>{unchanged.slice(0, 6).join(" · ") || "—"}</div>
          </div>
        </div>
      )}
    </div>
  );
}
