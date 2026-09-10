import { useState } from "react";
import { useSimulation } from "../hooks/useSimulation.jsx";

const ACTIONS = ["NO_ACTION", "REVOKE_CREDENTIALS", "ISOLATE_ENDPOINT", "BLOCK_NETWORK_PATH", "ISOLATE_AND_REVOKE"];

export default function CounterfactualReplay() {
  const { state, actions, busy } = useSimulation();
  const [action, setAction] = useState("ISOLATE_AND_REVOKE");
  const [index, setIndex] = useState(3);
  const last = state?.last_counterfactual;
  const replay = state?.incident_replay || {};

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Counterfactual Replay</h1>
      <p className="text-sm text-soc-muted">Safe state-transition what-ifs on the same incident. SIMULATED / ESTIMATED.</p>
      <div className="panel flex flex-wrap items-end gap-3 p-4">
        <label className="text-sm">
          Action
          <select className="mt-1 block rounded-lg border border-soc-border bg-soc-bg p-2" value={action} onChange={(e) => setAction(e.target.value)}>
            {ACTIONS.map((a) => <option key={a}>{a}</option>)}
          </select>
        </label>
        <label className="text-sm">
          Intervention index
          <input type="number" min={0} max={7} className="mt-1 block rounded-lg border border-soc-border bg-soc-bg p-2" value={index} onChange={(e) => setIndex(Number(e.target.value))} />
        </label>
        <button className="btn btn-primary" disabled={!!busy} onClick={() => actions.counterfactual({ action, intervention_index: index })}>
          Run counterfactual
        </button>
      </div>
      {last ? (
        <div className="grid gap-3 md:grid-cols-6">
          <Stat k="Systems affected" v={last.systems_affected} />
          <Stat k="Exposure" v={last.exposure} />
          <Stat k="Downtime" v={last.downtime} />
          <Stat k="Impact" v={last.impact_level} />
          <Stat k="Containment" v={last.containment} />
          <Stat k="Recovery" v={last.recovery} />
        </div>
      ) : (
        <div className="panel p-4 text-sm text-soc-muted">Run a counterfactual to populate metrics from the engine.</div>
      )}
      <div className="panel p-4">
        <div className="mb-2 text-xs uppercase text-soc-muted">Incident replay</div>
        <div className="flex flex-wrap gap-2">
          <button className="btn btn-ghost" onClick={() => actions.replay({ command: "PLAY" })}>Play</button>
          <button className="btn btn-ghost" onClick={() => actions.replay({ command: "PAUSE" })}>Pause</button>
          <button className="btn btn-ghost" onClick={() => actions.replay({ command: "REPLAY" })}>Replay</button>
          <button className="btn btn-ghost" onClick={() => actions.replay({ command: "PREVIOUS" })}>Previous</button>
          <button className="btn btn-ghost" onClick={() => actions.replay({ command: "NEXT" })}>Next</button>
          <button className="btn btn-ghost" onClick={() => actions.replay({ command: "PLAY", speed: 2 })}>Speed 2x</button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {(replay.stages || []).map((s, i) => (
            <button key={s} className="rounded-lg border border-soc-border px-3 py-2 text-xs" onClick={() => actions.replay({ command: "SEEK", index: i })}>
              {s}
            </button>
          ))}
        </div>
        {replay.focus?.event ? (
          <div className="mt-4 grid gap-3 md:grid-cols-3 text-sm">
            <div className="rounded-lg bg-soc-raised p-3">
              <div className="text-xs text-soc-muted">What did the defender know?</div>
              {(replay.focus.defender_knew || []).join(", ")}
            </div>
            <div className="rounded-lg bg-soc-raised p-3">
              <div className="text-xs text-soc-muted">What action was available?</div>
              {replay.focus.available_action}
            </div>
            <div className="rounded-lg bg-soc-raised p-3">
              <div className="text-xs text-soc-muted">What would have happened?</div>
              {replay.focus.would_have_happened ? `${replay.focus.would_have_happened.systems_affected} systems, exposure ${replay.focus.would_have_happened.exposure} (${replay.focus.would_have_happened.label})` : "—"}
            </div>
          </div>
        ) : (
          <p className="mt-3 text-sm text-soc-muted">Advance replay to inspect defender knowledge at each stage.</p>
        )}
      </div>
    </div>
  );
}

function Stat({ k, v }) {
  return (
    <div className="panel p-3">
      <div className="text-xs text-soc-muted">{k}</div>
      <div className="text-xl font-semibold">{v}</div>
    </div>
  );
}
