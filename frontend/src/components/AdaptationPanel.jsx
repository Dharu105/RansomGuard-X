import { fmt } from "../utils/format.js";
import { EmptyState, MetaBadge } from "./ui.jsx";
import { useState } from "react";

function classTone(cls) {
  if (cls === "ROBUST") return "text-soc-good";
  if (cls === "MODERATE") return "text-soc-warn";
  if (cls === "FRAGILE") return "text-soc-crit";
  return "text-soc-muted";
}

export default function AdaptationPanel({ adaptation }) {
  const a = adaptation || {};
  const scenarios = a.scenarios || [];
  const comparisons = a.comparisons || [];
  const has = Boolean(a.defense_action);
  const score = Number(a.robustness_score || 0);
  const [level, setLevel] = useState(null);
  const selected = scenarios.find((s) => String(s.adaptation_level) === String(level)) || scenarios[scenarios.length - 1];

  return (
    <div className="panel p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-soc-muted">Attacker adaptation test</div>
        <MetaBadge tone="purple">Simulated adaptation</MetaBadge>
      </div>
      <p className="mt-1 text-sm text-soc-muted">Test whether the defense remains effective when the attacker adapts.</p>
      <p className="text-[11px] text-soc-muted">{a.label || "SIMULATED adaptation — not a real attacker"}</p>

      {has ? (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <div className="rounded-lg bg-soc-raised p-3">
              <div className="text-[10px] uppercase text-soc-muted">Adaptation level</div>
              <div className="text-lg font-semibold">{scenarios[scenarios.length - 1]?.adaptation_level || a.adaptation_level || "n/a"}</div>
            </div>
            <div className="rounded-lg bg-soc-raised p-3">
              <div className="text-[10px] uppercase text-soc-muted">Robustness score</div>
              <div className="font-mono text-2xl font-semibold">{fmt(score)} / 100</div>
              <div className="mt-2 h-1.5 overflow-hidden rounded bg-soc-border">
                <div className="h-full bg-violet-500 transition-all duration-300" style={{ width: `${Math.max(0, Math.min(100, score))}%` }} />
              </div>
            </div>
            <div className="rounded-lg bg-soc-raised p-3">
              <div className="text-[10px] uppercase text-soc-muted">Classification</div>
              <div className={`text-lg font-semibold ${classTone(a.robustness_class)}`}>{a.robustness_class || "UNCERTAIN"}</div>
            </div>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-soc-border p-3 text-sm">
              <div>Original target: <b className="font-mono">{a.original_target || "none"}</b></div>
              <div>Protected: <b className="font-mono">{a.protected_target || "none"}</b></div>
              <div className="mt-2 text-[10px] uppercase text-soc-muted">Alternate path / target</div>
              <div className="font-mono">{(a.alternate_targets && a.alternate_targets[0]) || a.alternate_path || "none"}</div>
            </div>
            <p className="text-sm text-soc-muted">{a.summary}</p>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {scenarios.map((s) => (
              <button
                type="button"
                key={s.adaptation_level}
                onClick={() => setLevel(s.adaptation_level)}
                className={`rounded-lg border px-3 py-1 text-sm ${
                  selected && s.adaptation_level === selected.adaptation_level
                    ? "border-violet-500/50 bg-violet-500/10 text-violet-300"
                    : "border-soc-border text-soc-muted"
                }`}
              >
                {s.adaptation_level}
              </button>
            ))}
          </div>
          {selected ? (
            <div className="mt-3 rounded-lg border border-violet-500/20 bg-soc-raised p-3 text-sm">
              <div>Projected risk {fmt(selected.projected_risk)} · Blast {selected.blast_radius} · {selected.outcome}</div>
              {selected.alternate_target ? (
                <div className="mt-2 font-mono">
                  {(a.original_target || a.protected_target || "TARGET")}
                  <div className="text-soc-muted">↓</div>
                  {selected.alternate_target}
                </div>
              ) : null}
            </div>
          ) : null}
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {scenarios.map((s) => (
              <div key={s.adaptation_level} className="rounded-lg border border-soc-border p-3">
                <div className="text-[10px] uppercase text-soc-muted">{s.adaptation_level} adaptation</div>
                <div className="font-mono text-lg font-semibold">{s.adaptation_score}</div>
                <div className="mt-2 text-sm">Projected risk {fmt(s.projected_risk)}</div>
                <div className="text-sm">Blast {s.blast_radius}</div>
                <div className="text-sm">Outcome {s.outcome}</div>
                {s.alternate_target ? <div className="font-mono text-xs text-soc-muted">Alternate {s.alternate_target}</div> : null}
              </div>
            ))}
          </div>
          {comparisons.length > 0 && (
            <div className="mt-4 overflow-x-auto">
              <div className="text-[10px] uppercase text-soc-muted">Defense robustness comparison</div>
              <table className="mt-2 w-full text-left text-sm">
                <thead className="text-xs text-soc-muted">
                  <tr>
                    <th className="py-1">Defense</th>
                    <th>Robustness</th>
                    <th>Classification</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisons.map((c) => (
                    <tr key={c.defense_action} className={c.defense_action === a.defense_action ? "bg-violet-500/10" : ""}>
                      <td className="py-1">{c.title}</td>
                      <td className="font-mono">{fmt(c.robustness_score)}</td>
                      <td className={classTone(c.robustness_class)}>{c.robustness_class}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      ) : (
        <div className="mt-3">
          <EmptyState title="No adaptation analysis" body="No adaptation analysis until synthetic events produce a defense." />
        </div>
      )}
    </div>
  );
}
