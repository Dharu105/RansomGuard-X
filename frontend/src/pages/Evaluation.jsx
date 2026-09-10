import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../services/api.js";
import EvaluationPanel from "../components/EvaluationPanel.jsx";
import { MetaBadge, PageHeader } from "../components/ui.jsx";
import { useSimulation } from "../hooks/useSimulation.jsx";

export default function Evaluation() {
  const { state, actions, busy } = useSimulation();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api
      .evaluation()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const rows = data
    ? Object.keys(data.ransomguard_x || {}).map((k) => ({
        metric: k,
        baseline: data.rule_based_baseline[k],
        rgx: data.ransomguard_x[k],
      }))
    : [];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Evaluation"
        subtitle={`${data?.label || "SIMULATION / EXPERIMENTAL"} · Synthetic evaluation only. Not a production accuracy claim.`}
        badges={<MetaBadge tone="cyan">Synthetic evaluation</MetaBadge>}
      />
      <EvaluationPanel
        evaluation={data || state?.evaluation}
        busy={busy || (loading ? "load" : "")}
        onRun={() => actions.runEvaluation().then(load)}
        onReset={() => actions.resetEvaluation().then(load)}
      />
      <button className="btn btn-ghost" onClick={load} disabled={loading}>
        {loading ? "Loading…" : "Refresh metrics"}
      </button>
      {error ? <div className="text-soc-crit text-sm">{error}</div> : null}
      {data?.charts ? (
        <div className="panel h-72 p-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.charts}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1D2938" />
              <XAxis dataKey="metric" stroke="#7E8A9A" />
              <YAxis stroke="#7E8A9A" />
              <Tooltip />
              <Legend />
              <Bar dataKey="baseline" fill="#64748b" name="Typical traditional workflow" />
              <Bar dataKey="rgx" fill="#22D3EE" name="RansomGuard-X" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : null}
      {rows.length > 0 ? (
        <div className="panel overflow-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-soc-muted">
              <tr>
                <th className="p-3">Metric</th>
                <th>Typical traditional workflow</th>
                <th>RansomGuard-X</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.metric} className="border-t border-soc-border">
                  <td className="p-3">{r.metric}</td>
                  <td>{String(r.baseline)}</td>
                  <td>{String(r.rgx)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
