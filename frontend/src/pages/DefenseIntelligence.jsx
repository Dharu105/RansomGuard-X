import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useSimulation } from "../hooks/useSimulation.jsx";
import { fmt } from "../utils/format.js";

export default function DefenseIntelligence() {
  const { state, actions, busy } = useSimulation();
  const rob = state?.robustness || {};
  const missed = state?.missed_impact || {};
  const regret = state?.defense_regret_detail || {};
  const pvr = state?.prediction_vs_reality || {};
  const chart = (rob.trials || []).map((t) => ({ rate: `${t.rate}%`, top: t.top, score: t.scores?.[state?.recommended_defense?.action] || 0 }));

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Defense Intelligence</h1>
      <p className="text-sm text-soc-muted">Robustness, missed impact, regret, and prediction vs reality. Experimental simulation only.</p>
      <div className="flex flex-wrap gap-2">
        <button className="btn btn-primary" disabled={!!busy} onClick={() => actions.robustness({ rates: [30, 50, 70, 90] })}>
          Test robustness
        </button>
        <button className="btn btn-ghost" disabled={!!busy} onClick={() => actions.dropEvent("credential_access")}>
          Remove credential-access event
        </button>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <div className="panel p-4">
          <div className="text-xs uppercase text-soc-muted">Robustness</div>
          <div className="mt-2 text-2xl font-semibold">{rob.verdict || "Not tested"}</div>
          <p className="text-sm text-soc-muted">{rob.note || rob.label}</p>
        </div>
        <div className="panel p-4">
          <div className="text-xs uppercase text-soc-muted">Defense regret</div>
          <div className="mt-2 text-2xl font-semibold">{fmt(state?.defense_regret)}</div>
          <p className="text-sm text-soc-muted">{regret.reason || "Approve a defense to store regret on the incident."}</p>
        </div>
        <div className="panel p-4">
          <div className="text-xs uppercase text-soc-muted">Missed impact</div>
          <p className="mt-2 text-sm">Avoidable systems: {missed.avoidable_systems ?? "—"}</p>
          <p className="text-sm">Avoidable exposure: {missed.avoidable_exposure ?? "—"}</p>
          <p className="text-sm">Avoidable downtime: {missed.avoidable_downtime ?? "—"}</p>
          <p className="text-xs text-soc-muted">{missed.label || "SIMULATED ESTIMATE"}</p>
        </div>
      </div>
      {chart.length ? (
        <div className="panel p-4 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#243044" />
              <XAxis dataKey="rate" stroke="#8BA0B5" />
              <YAxis stroke="#8BA0B5" />
              <Tooltip />
              <Legend />
              <Bar dataKey="score" fill="#3A7CA5" name="Recommended score vs adaptation" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : null}
      {state?.robustness_signal ? (
        <div className="panel p-4 text-sm">
          Removed {state.robustness_signal.removed}: confidence {state.robustness_signal.confidence_before} → {state.robustness_signal.confidence_after} (drop {state.robustness_signal.drop}).
          <div className="text-soc-warn">{state.robustness_signal.note}</div>
        </div>
      ) : null}
      <div className="panel p-4 text-sm">
        <div className="text-xs uppercase text-soc-muted">Prediction vs reality</div>
        {pvr.predicted_target ? (
          <div className="mt-2">
            Predicted {pvr.predicted_target} vs actual {pvr.actual_target} · confidence {pvr.prediction_confidence} · {pvr.correct ? "CORRECT" : "INCORRECT / pending completion"}
          </div>
        ) : (
          <p className="mt-2 text-soc-muted">Complete the event stream to compare predicted and actual targets.</p>
        )}
      </div>
      <div className="panel p-4 text-sm">
        <div className="text-xs uppercase text-soc-muted">Uncertainty ranges</div>
        <p className="mt-2">Next target: {state?.uncertainty?.next_target || "—"} ({(state?.uncertainty?.confidence_range || []).join("–") || "n/a"}%)</p>
        {(state?.uncertainty?.defense_ranges || []).map((d) => (
          <div key={d.action}>{d.action}: {(d.range || []).join("–")}%</div>
        ))}
      </div>
    </div>
  );
}
