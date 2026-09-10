import { fmt } from "../utils/format.js";
import { MetaBadge } from "./ui.jsx";

export default function HeroIntel({ prediction, currentNode, defense, onReview, busy, onOpenDefense, onOpenPredict, idle }) {
  const p = prediction || {};
  const d = defense || {};
  const rec = (d.options || []).find((o) => o.action === d.recommended_action);
  const hasPred = Boolean(p.predicted_target);
  const hasDef = Boolean(d.recommended_action);

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="intel-radar relative min-h-[210px] overflow-hidden rounded-xl border border-indigo-500/25 bg-[#0b1220] p-4">
        {hasPred ? <div className="sweep" aria-hidden="true" /> : null}
        <div className="relative z-10">
          <div className="flex items-center justify-between gap-2">
            <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-indigo-300">Threat forecast</div>
            <MetaBadge tone="blue">Prediction — not observed reality</MetaBadge>
          </div>
          {idle || !hasPred ? (
            <p className="mt-4 text-sm text-soc-muted">The intelligence layer is idle until observed events produce a forecast.</p>
          ) : (
            <>
              <div className="mt-3 text-[10px] uppercase text-soc-muted">Target</div>
              <div className="font-mono text-xl font-semibold text-indigo-200">{p.predicted_target}</div>
              <div className="mt-1 font-mono text-4xl font-semibold text-blue-400">{fmt(p.confidence || 0)}</div>
              <div className="font-mono text-xs text-soc-muted">{p.predicted_action}</div>
              <div className="mt-3 text-[10px] uppercase text-soc-muted">Why this target?</div>
              <ul className="mt-1 space-y-1 text-[11px] text-soc-muted">
                {(p.evidence || []).slice(0, 4).map((item) => (
                  <li key={item}>✓ {item}</li>
                ))}
              </ul>
              <div className="mt-2 text-[11px] text-soc-muted">Looking ahead from {currentNode || p.current_node || "none"}</div>
              <button type="button" className="btn btn-ghost mt-3 py-1 text-xs" onClick={onOpenPredict}>
                Open forecast
              </button>
            </>
          )}
        </div>
      </div>

      <div className="flex-1 rounded-xl border border-amber-500/20 bg-[#0b1220] p-4">
        <div className="flex items-center justify-between gap-2">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-soc-muted">Defense intelligence</div>
          <MetaBadge tone="amber">Human approval required</MetaBadge>
        </div>
        {!hasDef ? (
          <p className="mt-3 text-sm text-soc-muted">No tactical recommendation until the incident produces a meaningful threat.</p>
        ) : (
          <>
            <div className="mt-2 text-[10px] uppercase text-soc-muted">Recommended</div>
            <div className="font-mono text-lg font-semibold">{d.recommended_action}</div>
            {rec ? (
              <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
                <div>Current risk <div className="font-mono text-sm">{fmt(rec.risk_before)}</div></div>
                <div>Projected <div className="font-mono text-sm text-soc-good">{fmt(rec.risk_after)}</div></div>
                <div>Blast radius <div>{rec.blast_radius_before} → {rec.blast_radius_after}</div></div>
                <div>Disruption <div>{rec.operational_disruption}</div></div>
              </div>
            ) : null}
            <button type="button" className="btn btn-primary mt-3 py-1.5 text-xs" disabled={!!busy} onClick={() => onReview && onReview(d.recommended_action)}>
              Review decision
            </button>
            <button type="button" className="btn btn-ghost mt-2 py-1 text-xs" onClick={onOpenDefense}>
              Compare options
            </button>
          </>
        )}
      </div>
    </div>
  );
}
