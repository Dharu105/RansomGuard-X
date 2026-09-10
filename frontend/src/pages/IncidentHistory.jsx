import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../services/api.js";

export default function IncidentHistory() {
  const [incidents, setIncidents] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    Promise.all([api.incidents(), api.historyMetrics()])
      .then(([a, b]) => {
        setIncidents(a.incidents || []);
        setMetrics(b);
      })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold tracking-tight">Incident Memory</h1>
      <p className="text-sm text-soc-muted">Seeded INC-001 / INC-002 / INC-003 plus the live incident. Charts are SIMULATED / EXPERIMENTAL.</p>
      {error ? <div className="text-soc-crit text-sm">{error}</div> : null}
      <div className="panel overflow-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs text-soc-muted">
            <tr>
              <th className="p-3">ID</th>
              <th>Title</th>
              <th>Risk</th>
              <th>Assets</th>
              <th>Response</th>
              <th>Regret</th>
              <th>Best CF</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((r) => (
              <tr key={r.id} className="cursor-pointer border-t border-soc-border hover:bg-soc-raised" onClick={() => setSelected(r)}>
                <td className="p-3 font-medium">{r.id}</td>
                <td>{r.title}</td>
                <td>{r.risk_score}</td>
                <td>{(r.affected_assets || []).join(", ")}</td>
                <td>{r.recommended_action}</td>
                <td>{r.defense_regret}</td>
                <td>{r.counterfactual_results?.[0]?.action || "ISOLATE_AND_REVOKE"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selected ? (
        <div className="panel p-4 text-sm">
          <div className="font-semibold">{selected.id} · {selected.title}</div>
          <div>Stage {selected.attack_stage} · status {selected.status} · estimated impact from outcome {JSON.stringify(selected.actual_outcome)}</div>
          <div className="text-soc-muted">Playbook learning stored in defense memory for this pattern.</div>
        </div>
      ) : null}
      {metrics ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Chart title="Defense effectiveness" data={metrics.defense_effectiveness} dataKey="value" xKey="id" />
          <Chart title="Propagation reduction" data={metrics.propagation_reduction} dataKey="value" xKey="id" />
          <Chart title="False positives" data={metrics.false_positives} dataKey="value" xKey="name" />
          <div className="panel p-4 h-64">
            <div className="text-xs text-soc-muted">MTTD / MTTR / recommendation improvement</div>
            <ResponsiveContainer width="100%" height="90%">
              <LineChart data={metrics.recommendation_improvement}>
                <CartesianGrid strokeDasharray="3 3" stroke="#243044" />
                <XAxis dataKey="id" stroke="#8BA0B5" />
                <YAxis stroke="#8BA0B5" />
                <Tooltip />
                <Legend />
                <Line dataKey="value" stroke="#3D9A7A" name="Recommendation quality" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Chart({ title, data, dataKey, xKey }) {
  return (
    <div className="panel p-4 h-64">
      <div className="text-xs text-soc-muted">{title}</div>
      <ResponsiveContainer width="100%" height="90%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#243044" />
          <XAxis dataKey={xKey} stroke="#8BA0B5" />
          <YAxis stroke="#8BA0B5" />
          <Tooltip />
          <Bar dataKey={dataKey} fill="#3A7CA5" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
