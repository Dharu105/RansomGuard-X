import { fmt } from "../utils/format.js";
import { EmptyState, MetaBadge } from "./ui.jsx";
import { useState } from "react";

export default function AttackForkLab({ forksPayload, busy, onReview }) {
  const payload = forksPayload || {};
  const current = payload.current_state || {};
  const forks = payload.forks || [];
  const best = payload.best_fork;
  const has = forks.length > 0;
  const [focus, setFocus] = useState(best?.fork_id || forks[0]?.fork_id || "");
  const selected = forks.find((f) => f.fork_id === focus) || forks[0];

  return (
    <div className="panel p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-soc-muted">Attack Fork Lab</div>
        <MetaBadge tone="mute">Read-only simulation</MetaBadge>
      </div>
      <p className="mt-1 text-sm text-soc-muted">Simulate defensive futures before committing. Live state is not mutated.</p>
      <p className="text-[11px] text-soc-muted">{payload.label || "SIMULATED attack forks — not applied"}</p>

      {has ? (
        <>
          <div className="mt-4 text-center text-[10px] uppercase tracking-wide text-soc-muted">Current state</div>
          <div className="mx-auto max-w-md rounded-lg border border-soc-border bg-soc-raised p-3 text-center font-mono text-sm">
            {current.current_node || "none"} · risk {fmt(current.risk || 0)}
          </div>
          <div className="my-1 text-center text-soc-muted">│</div>
          <div className="grid gap-3 md:grid-cols-3">
            {forks.map((f) => (
              <button
                type="button"
                key={f.fork_id}
                onClick={() => setFocus(f.fork_id)}
                className={`rounded-lg border p-3 text-left transition duration-200 ${
                  f.fork_id === (selected?.fork_id) ? "border-cyan-500/50 bg-cyan-500/5" : f.is_best ? "border-soc-good/40" : "border-soc-border hover:bg-soc-raised"
                }`}
              >
                <div className="text-[10px] uppercase text-soc-muted">{f.is_best ? "Best fork" : `Fork ${f.label}`}</div>
                <div className="font-mono text-sm font-semibold">{f.defense_action}</div>
                <div className="my-1 text-center text-[10px] text-soc-muted">↓</div>
                <div className="text-sm">Risk {fmt(f.projected_risk)}</div>
                <div className="text-xs text-soc-muted">Adapt {f.projected_next_target || "NONE"}</div>
              </button>
            ))}
          </div>
          {selected ? (
            <div className="mt-4 rounded-lg border border-soc-border bg-soc-raised p-4">
              <div className="font-semibold">{selected.title}</div>
              <div className="mt-2 grid gap-2 text-sm md:grid-cols-4">
                <div>Risk {fmt(selected.risk_before)} → {fmt(selected.projected_risk)}</div>
                <div>Blast {selected.blast_radius_before} → {selected.blast_radius_after}</div>
                <div>Disruption {selected.operational_disruption}</div>
                <div>Robustness {selected.robustness || selected.reversibility}</div>
              </div>
              <p className="mt-2 text-sm text-soc-muted">{selected.summary}</p>
            </div>
          ) : null}

          {best && (
            <div className="mt-4 rounded-lg border border-soc-good/50 bg-soc-good/10 p-4">
              <div className="text-[10px] uppercase tracking-wide text-soc-muted">Best simulated future</div>
              <div className="text-xl font-semibold">{best.title}</div>
              <div className="text-sm">{best.defense_action} · Fork score {fmt(best.fork_score)}</div>
              <p className="mt-2 text-sm">{best.why || best.summary}</p>
              <button className="btn btn-primary mt-3" disabled={!!busy} onClick={() => onReview && onReview(best.defense_action)}>
                Review this defense
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="mt-3">
          <EmptyState title="No forks yet" body="No forks until synthetic events produce a defense recommendation." />
        </div>
      )}
    </div>
  );
}
