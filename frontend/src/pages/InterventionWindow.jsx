import { useSimulation } from "../hooks/useSimulation.jsx";

export default function InterventionWindow() {
  const { state, actions, busy } = useSimulation();
  const window = state?.intervention_window || {};
  const selected = state?.selected_intervention;
  const idx = selected?.index ?? window.best_index ?? 3;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold tracking-tight">Intervention Window</h1>
      <p className="text-sm text-soc-muted">Impact is computed by the simulation engine. Values are SIMULATED / ESTIMATED.</p>
      <div className="panel p-4">
        <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-soc-muted">When should we intervene?</div>
        <div className="flex justify-between text-[10px] uppercase text-soc-muted">
          <span>Early</span>
          <span>Current</span>
          <span>Late</span>
        </div>
        <div className="relative mt-2 h-2 rounded-full bg-soc-raised">
          <div className="absolute top-1/2 h-3 w-3 -translate-y-1/2 rounded-full bg-cyan-400" style={{ left: `${(idx / 7) * 100}%` }} />
        </div>
        <input
          type="range"
          min={0}
          max={7}
          value={idx}
          disabled={!!busy}
          onChange={(e) => actions.intervention(Number(e.target.value))}
          className="w-full"
        />
        <div className="mt-2 flex justify-between text-xs text-soc-muted">
          {(window.timeline || []).map((t) => (
            <span key={t.index}>{t.time}</span>
          ))}
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-5">
        {(window.timeline || []).map((t) => (
          <button
            key={t.index}
            className={`panel p-3 text-left ${idx === t.index ? "ring-1 ring-soc-accent" : ""}`}
            onClick={() => actions.intervention(t.index)}
          >
            <div className="text-xs text-soc-muted">{t.time}</div>
            <div className="font-semibold">{t.classification}</div>
            <div className="text-xs">{t.event}</div>
            <div className="mt-2 text-xs text-soc-muted">
              systems {t.impact?.systems_affected} · exposure {t.impact?.exposure}
            </div>
          </button>
        ))}
      </div>
      <div className="panel p-4">
        <div className="text-xs uppercase text-soc-muted">Last safe intervention</div>
        <div className="mt-2 text-lg font-semibold">
          {window.last_safe_intervention?.time || "10:03"} · {window.last_safe_intervention?.classification || "BEST"}
        </div>
        {selected?.impact ? (
          <div className="mt-3 text-sm">
            At {selected.time} ({selected.classification}): {selected.impact.systems_affected} systems, downtime {selected.impact.downtime},
            containment {selected.impact.containment}. {selected.impact.label}
          </div>
        ) : (
          <div className="mt-3 text-sm text-soc-muted">Move the slider to recompute impact for an intervention time.</div>
        )}
      </div>
    </div>
  );
}
