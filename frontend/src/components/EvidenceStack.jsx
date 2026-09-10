import { useState } from "react";

export default function EvidenceStack({ items }) {
  const [open, setOpen] = useState(null);
  const rows = items || [];
  if (!rows.length) return <p className="text-sm text-soc-muted">No evidence yet.</p>;
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {rows.map((item, i) => {
        const key = typeof item === "string" ? item : item.id || item.text || i;
        const title = typeof item === "string" ? item : item.text || item.event || item.title;
        const asset = typeof item === "object" ? item.asset || item.asset_id : null;
        const expanded = open === key;
        return (
          <button
            type="button"
            key={key}
            onClick={() => setOpen(expanded ? null : key)}
            className="rounded-md border border-cyan-500/20 bg-[#0c1422] px-3 py-2 text-left text-sm transition duration-200 hover:-translate-y-0.5 hover:border-cyan-400/40"
          >
            <div className="text-[10px] uppercase tracking-wide text-cyan-400">Evidence</div>
            <div className="mt-1 font-medium">✓ {title}</div>
            {asset ? <div className="font-mono text-[11px] text-soc-muted">{asset}</div> : null}
            {expanded ? (
              <div className="mt-2 space-y-1 font-mono text-[11px] text-soc-muted">
                <div>Event {typeof item === "object" ? item.event || title : title}</div>
                {typeof item === "object" && (item.stage || item.attack_stage) ? <div>Stage {item.stage || item.attack_stage}</div> : null}
                {typeof item === "object" && (item.effect || item.reason) ? <div>Impact {item.effect || item.reason}</div> : null}
                {typeof item === "object" && item.source ? <div>Source {item.source}</div> : null}
                <div>Why it matters: used as observed decision evidence, not a predicted future.</div>
              </div>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
