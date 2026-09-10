import { useState } from "react";
import { useSimulation } from "../hooks/useSimulation.jsx";

export default function AlternateReality() {
  const { state, actions, busy } = useSimulation();
  const alt = state?.alternate_realities || {};
  const [focus, setFocus] = useState("actual_reality");
  const cards = [
    ["actual_reality", "ACTUAL REALITY", alt.actual_reality],
    ["scenario_a", "SCENARIO A", alt.scenario_a],
    ["scenario_b", "SCENARIO B", alt.scenario_b],
    ["scenario_c", "SCENARIO C", alt.scenario_c],
  ];
  const selected = alt[focus];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Alternate Reality</h1>
      <p className="text-sm text-soc-muted">Side-by-side simulated worlds from the same incident engine.</p>
      <button
        className="btn btn-primary"
        disabled={!!busy}
        onClick={() => actions.counterfactual({ action: "ISOLATE_AND_REVOKE", intervention_index: 3 })}
      >
        Generate alternate realities
      </button>
      <div className="grid gap-3 md:grid-cols-4">
        {cards.map(([key, title, data]) => (
          <button key={key} onClick={() => setFocus(key)} className={`panel p-4 text-left ${focus === key ? "ring-1 ring-soc-accent" : ""}`}>
            <div className="text-xs text-soc-muted">{title}</div>
            {data ? (
              <>
                <div className="mt-2 font-semibold">{data.action}</div>
                <div className="text-sm">Systems {data.systems_affected}</div>
                <div className="text-sm">Exposure {data.exposure}</div>
                <div className="text-sm">Downtime {data.downtime}</div>
                <div className="text-xs text-soc-muted">{data.label || "SIMULATED / ESTIMATED"}</div>
              </>
            ) : (
              <div className="mt-2 text-sm text-soc-muted">Approve or run counterfactual to populate.</div>
            )}
          </button>
        ))}
      </div>
      <div className="panel p-4">
        <div className="text-xs uppercase text-soc-muted">Inspected path</div>
        {selected ? (
          <div className="mt-2 text-sm">
            {(selected.affected_assets || []).join(" → ") || "n/a"}
            <div className="mt-2 text-soc-muted">Impact {selected.impact_level} · containment {selected.containment} · recovery {selected.recovery}</div>
          </div>
        ) : (
          <p className="mt-2 text-sm text-soc-muted">Select a scenario card.</p>
        )}
      </div>
      <div className="panel p-4">
        <div className="text-xs uppercase text-soc-muted">Adaptive attacker</div>
        {state?.adaptive_paths?.original_path ? (
          <div className="mt-2 grid gap-3 md:grid-cols-3 text-sm">
            <Path title="Original path" items={state.adaptive_paths.original_path} />
            <Path title="Blocked path" items={state.adaptive_paths.blocked_path} />
            <Path title="Alternative path" items={state.adaptive_paths.alternative_path} />
            <p className="md:col-span-3 text-soc-muted">{state.adaptive_paths.narrative}</p>
          </div>
        ) : (
          <p className="mt-2 text-sm text-soc-muted">Approve a defense to simulate attacker adaptation.</p>
        )}
      </div>
    </div>
  );
}

function Path({ title, items }) {
  return (
    <div className="rounded-lg bg-soc-raised p-3">
      <div className="text-xs text-soc-muted">{title}</div>
      <div className="mt-1">{(items || []).join(" → ") || "—"}</div>
    </div>
  );
}
