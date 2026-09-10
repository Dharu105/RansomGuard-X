import { LOOP_STAGES } from "../types/index.js";

const map = {
  OBSERVE: "DETECT",
  DETECT: "DETECT",
  UNDERSTAND: "UNDERSTAND",
  PREDICT: "PREDICT",
  DECIDE: "DECIDE",
  DEFEND: "DEFEND",
  REPLAY: "REPLAY",
  COMPARE: "COMPARE",
  LEARN: "LEARN",
};

export default function ClosedLoop({ stage }) {
  const current = map[stage] || "DETECT";
  return (
    <div className="panel p-4">
      <div className="mb-3 text-[10px] uppercase tracking-[0.16em] text-soc-muted">Closed defense loop</div>
      <div className="flex flex-wrap items-center gap-2">
        {LOOP_STAGES.map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div
              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                s === current ? "bg-cyan-500/20 text-cyan-400" : "bg-soc-raised text-soc-muted"
              }`}
            >
              {s}
            </div>
            {i < LOOP_STAGES.length - 1 ? <span className="text-soc-muted">→</span> : <span className="text-soc-muted">↺</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
