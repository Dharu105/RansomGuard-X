import { EmptyState, MetaBadge } from "./ui.jsx";

function Metric({ label, value, large }) {
  const text = value === null || value === undefined ? "—" : String(value);
  return (
    <div className="rounded-lg bg-soc-raised p-3">
      <div className="text-[10px] uppercase tracking-wide text-soc-muted">{label}</div>
      <div className={`mt-1 font-mono font-semibold ${large ? "text-3xl" : "text-lg"}`}>{text}</div>
    </div>
  );
}

export default function EvaluationPanel({ evaluation, busy, onRun, onReset }) {
  const ev = evaluation || {};
  const report = ev.report || ev;
  const det = report.detection_metrics || ev.detection_metrics || {};
  const pred = report.prediction_metrics || ev.prediction_metrics || {};
  const defn = report.defense_metrics || ev.defense_metrics || {};
  const adapt = report.adaptation_metrics || ev.adaptation_metrics || {};
  const timing = report.timing_metrics || ev.timing_metrics || {};
  const fp = report.false_positive_metrics || ev.false_positive_metrics || {};
  const base = report.baseline_comparison || ev.baseline_comparison || {};
  const loop = report.closed_loop_metrics || ev.closed_loop_metrics || {};
  const limits = report.limitations || ev.limitations || [];
  const scenarios = report.scenarios || ev.scenarios || [];
  const has = Boolean(report.evaluation_id || det.precision !== undefined);

  const meanEvents = (row) => {
    if (!row || row === "NOT_ENOUGH_DATA") return "NOT_ENOUGH_DATA";
    if (typeof row === "object") return row.mean_events;
    return row;
  };

  return (
    <div className="panel p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-soc-muted">Evaluation & Benchmarks</div>
          <div className="mt-2">
            <MetaBadge tone="cyan">Synthetic evaluation</MetaBadge>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-primary" type="button" disabled={!!busy} onClick={onRun}>
            Run evaluation
          </button>
          <button className="btn btn-ghost" type="button" disabled={!!busy} onClick={onReset}>
            Reset evaluation
          </button>
        </div>
      </div>

      {!has ? (
        <div className="mt-3">
          <EmptyState title="No evaluation report" body="Run the synthetic scenarios to measure the platform. Numbers are experimental, not production accuracy." />
        </div>
      ) : (
        <>
          <div className="mt-4">
            <div className="text-[10px] uppercase text-soc-muted">Detection</div>
            <div className="mt-2 grid gap-2 md:grid-cols-3">
              <Metric label="Precision" value={det.precision} large />
              <Metric label="Recall" value={det.recall} large />
              <Metric label="F1" value={det.f1} large />
            </div>
            <div className="mt-2 grid gap-2 md:grid-cols-4">
              <Metric label="TP" value={det.true_positives} />
              <Metric label="FP" value={det.false_positives} />
              <Metric label="TN" value={det.true_negatives} />
              <Metric label="FN" value={det.false_negatives} />
            </div>
          </div>
          {scenarios.length > 0 && (
            <div className="mt-4 overflow-x-auto">
              <div className="text-[10px] uppercase text-soc-muted">Scenario detection results</div>
              <table className="mt-2 w-full text-left text-sm">
                <thead className="text-xs text-soc-muted">
                  <tr>
                    <th className="py-1">Scenario</th>
                    <th>Expected</th>
                    <th>Observed</th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {scenarios.map((row) => (
                    <tr key={row.scenario_id}>
                      <td className="py-1 font-mono">{row.scenario_id}</td>
                      <td>{row.expected_class}</td>
                      <td>{row.classification}</td>
                      <td className={row.detection_result === "FN" ? "text-soc-crit" : ""}>{row.detection_result}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {scenarios.some((row) => row.detection_result === "FN") ? (
                <p className="mt-2 text-xs text-soc-crit">False negatives (including SCN-003 / SCN-004 when present) are shown as measured — not hidden.</p>
              ) : null}
            </div>
          )}
          <div className="mt-4">
            <div className="text-[10px] uppercase text-soc-muted">Prediction</div>
            <div className="mt-2 grid gap-2 md:grid-cols-4">
              <Metric label="Resolved" value={pred.resolved_predictions} />
              <Metric label="Correct" value={pred.correct_predictions} />
              <Metric label="Partial" value={pred.partial_predictions} />
              <Metric label="Incorrect" value={pred.incorrect_predictions} />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-[10px] uppercase text-soc-muted">Defense</div>
            <div className="mt-2 grid gap-2 md:grid-cols-3">
              <Metric label="Risk reduction" value={defn.average_risk_reduction} />
              <Metric label="Blast-radius reduction" value={defn.average_blast_radius_reduction} />
              <Metric label="Disruption" value={defn.average_disruption} />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-[10px] uppercase text-soc-muted">Adaptation</div>
            <div className="mt-2 grid gap-2 md:grid-cols-4">
              <Metric label="Robust" value={(adapt.distribution || {}).ROBUST} />
              <Metric label="Moderate" value={(adapt.distribution || {}).MODERATE} />
              <Metric label="Fragile" value={(adapt.distribution || {}).FRAGILE} />
              <Metric label="Uncertain" value={(adapt.distribution || {}).UNCERTAIN} />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-[10px] uppercase text-soc-muted">Event-based timing</div>
            <div className="mt-2 grid gap-2 md:grid-cols-4">
              <Metric label="Detection event" value={meanEvents(timing.first_detection_event)} />
              <Metric label="Defense review event" value={meanEvents(timing.first_defense_review)} />
              <Metric label="Approval event" value={meanEvents(timing.first_approval)} />
              <Metric label="Verification event" value={meanEvents(timing.containment_verification)} />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-[10px] uppercase text-soc-muted">False positives</div>
            <div className="mt-2 overflow-x-auto text-sm">
              <table className="w-full text-left">
                <thead className="text-xs text-soc-muted">
                  <tr>
                    <th className="py-1">Scenario</th>
                    <th>Expected</th>
                    <th>Observed</th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {(fp.rows || []).map((row) => (
                    <tr key={row.scenario}>
                      <td className="py-1 font-mono">{row.scenario}</td>
                      <td>{row.expected}</td>
                      <td>{row.observed}</td>
                      <td>{row.result}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
            <div>
              <div className="text-[10px] uppercase text-soc-muted">Typical traditional workflow</div>
              <ul className="mt-2 space-y-1">
                {Object.entries(base.traditional || {}).map(([k, v]) => (
                  <li key={k}>
                    {k}: {v}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="text-[10px] uppercase text-soc-muted">RansomGuard-X</div>
              <ul className="mt-2 space-y-1">
                {Object.entries(base.ransomguard_x || {}).map(([k, v]) => (
                  <li key={k}>
                    {k}: {v}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="mt-4 text-sm">
            <div className="text-[10px] uppercase text-soc-muted">Closed loop</div>
            <div className="mt-2 flex flex-wrap gap-2">
              <span>DETECT {loop.detection === "PASS" ? "✓" : "—"}</span>
              <span>PREDICT {loop.prediction === "PASS" ? "✓" : "—"}</span>
              <span>DEFEND {loop.defense === "PASS" ? "✓" : "—"}</span>
              <span>ADAPT {loop.adaptation === "PASS" ? "✓" : "—"}</span>
              <span>LEARN {loop.learning === "PASS" ? "✓" : "—"}</span>
              <span>EVOLVE {loop.playbook_evolution === "PASS" ? "✓" : "—"}</span>
            </div>
            <p className="mt-2 text-xs text-soc-muted">{loop.note}</p>
          </div>
        </>
      )}

      <div className="mt-4">
        <div className="text-[10px] uppercase text-soc-muted">Limitations</div>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-soc-muted">
          {(limits.length ? limits : ["synthetic scenarios", "no real-world accuracy claim"]).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
