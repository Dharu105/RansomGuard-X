import { bandColor, fmt } from "../utils/format.js";
import { EmptyState, MetaBadge } from "./ui.jsx";

export default function DetectionPanel({ detection }) {
  const d = detection || {};
  const evidence = d.evidence || [];
  return (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-3">
        <div className="panel p-4 md:col-span-1">
          <div className="text-[10px] uppercase tracking-wide text-soc-muted">Threat classification</div>
          <div className={`mt-2 text-2xl font-semibold ${bandColor(d.risk_level)}`}>
            {d.classification || "NORMAL"}
          </div>
          <div className="mt-2">
            <MetaBadge tone="mute">{d.label || "SIMULATION / EXPERIMENTAL"}</MetaBadge>
          </div>
        </div>
        <div className="panel p-4">
          <div className="text-[10px] uppercase tracking-wide text-soc-muted">Risk score</div>
          <div className="mt-2 font-mono text-4xl font-semibold">
            {fmt(d.risk_score ?? 0)} <span className="text-lg text-soc-muted">/ 100</span>
          </div>
        </div>
        <div className="panel p-4">
          <div className="text-[10px] uppercase tracking-wide text-soc-muted">Risk level</div>
          <div className={`mt-2 text-2xl font-semibold ${bandColor(d.risk_level)}`}>{d.risk_level || "LOW"}</div>
          <div className="mt-1 text-sm text-soc-muted">Stage: {d.attack_stage || "NORMAL"}</div>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="panel p-4">
          <div className="text-[10px] uppercase tracking-wide text-soc-muted">Attack intent</div>
          <p className="mt-2 text-lg font-medium">{d.intent || "No malicious progression indicated"}</p>
          <p className="mt-2 text-sm text-soc-muted">{d.reason}</p>
          <div className="mt-3 text-sm">
            Confidence <span className="font-semibold">{fmt(d.confidence ?? 0)}%</span>
          </div>
        </div>
        <div className="panel p-4">
          <div className="text-[10px] uppercase tracking-wide text-soc-muted">Supporting evidence</div>
          {evidence.length === 0 ? (
            <EmptyState title="No supporting events" body="No supporting events observed yet." />
          ) : (
            <ul className="mt-2 space-y-1 text-sm">
              {evidence.map((item) => (
                <li key={item}>● {item}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
