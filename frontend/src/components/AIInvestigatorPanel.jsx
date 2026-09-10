import EvidenceStack from "./EvidenceStack.jsx";
import { sanitizeBrand } from "../utils/format.js";
import { EmptyState, KindBadge, MetaBadge } from "./ui.jsx";

export default function AIInvestigatorPanel({ investigator }) {
  const inv = investigator || {};
  const story = inv.attack_story || [];
  const evidence = inv.key_evidence || [];
  const risk = inv.current_risk || {};
  const pred = inv.prediction_explanation || {};
  const defn = inv.defense_explanation || {};
  const adapt = inv.adaptation_explanation || {};
  const learn = inv.learning_explanation || {};
  const play = inv.playbook_explanation || {};
  const questions = inv.recommended_investigation_questions || [];
  const uncertainty = inv.uncertainty || [];
  const has = Boolean(inv.incident_summary || story.length);

  return (
    <div className="panel p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-violet-400">AI Investigator</div>
        <MetaBadge tone="mute">{inv.label || "SIMULATION / EXPERIMENTAL"}</MetaBadge>
      </div>
      <p className="mt-1 text-sm text-soc-muted">Evidence-grounded incident analysis. It does not contain, approve, or execute security actions.</p>

      {!has ? (
        <div className="mt-3">
          <EmptyState title="No briefing yet" body="Run a synthetic scenario to generate an investigator briefing." />
        </div>
      ) : null}

      <section className="mt-4 rounded-lg bg-soc-raised p-3">
        <div className="text-[10px] uppercase tracking-wide text-soc-muted">What happened?</div>
        <p className="mt-1 text-sm">{sanitizeBrand(inv.incident_summary) || "No summary."}</p>
      </section>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <section className="rounded-lg border border-soc-border p-3">
          <div className="text-[10px] uppercase tracking-wide text-soc-muted">Attack story</div>
          {story.length === 0 ? (
            <p className="mt-2 text-sm text-soc-muted">No observed events.</p>
          ) : (
            <ol className="mt-2 space-y-2 text-sm">
              {story.map((s) => (
                <li key={s.event_id || s.step} className="flex gap-2">
                  <KindBadge kind={s.kind} />
                  <span>{sanitizeBrand(s.text)}</span>
                </li>
              ))}
            </ol>
          )}
        </section>
        <section className="rounded-lg border border-soc-border p-3">
          <div className="text-[10px] uppercase tracking-wide text-soc-muted">Evidence court</div>
          {evidence.length === 0 ? (
            <p className="mt-2 text-sm text-soc-muted">No evidence yet.</p>
          ) : (
            <div className="mt-2">
              <EvidenceStack
                items={evidence.slice(0, 8).map((e) => ({
                  text: sanitizeBrand(e.text),
                  source: e.source,
                  kind: e.kind,
                }))}
              />
            </div>
          )}
        </section>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <section className="rounded-lg bg-soc-raised p-3 text-sm">
          <div className="text-[10px] uppercase text-soc-muted">Why is it risky?</div>
          <div className="mt-1 font-semibold">
            {risk.risk_classification} · {risk.risk_score}
          </div>
          <div>Stage {risk.attack_stage || inv.current_stage}</div>
          <div className="font-mono">Node {risk.current_node || "none"}</div>
          <p className="mt-2 text-xs text-soc-muted">{risk.explanation}</p>
        </section>
        <section className="rounded-lg bg-soc-raised p-3 text-sm">
          <div className="text-[10px] uppercase text-soc-muted">What is predicted?</div>
          <div className="mt-1 flex items-center gap-2">
            <KindBadge kind="PREDICTED" />
            <span className="font-mono">{pred.predicted_target || "none"} / {pred.predicted_action || "none"}</span>
          </div>
          <p className="mt-2 text-xs text-soc-muted">{pred.explanation}</p>
        </section>
        <section className="rounded-lg bg-soc-raised p-3 text-sm">
          <div className="text-[10px] uppercase text-soc-muted">Why this defense?</div>
          <div className="mt-1 flex items-center gap-2">
            <KindBadge kind="SIMULATED" />
            <span className="font-mono">{defn.recommended_action || "none"}</span>
          </div>
          <p className="mt-2 text-xs text-soc-muted">{defn.explanation}</p>
        </section>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-3">
        <section className="rounded-lg border border-soc-border p-3 text-sm">
          <div className="text-[10px] uppercase text-soc-muted">What happens under adaptation?</div>
          <div className="mt-1 flex items-center gap-2">
            <KindBadge kind="SIMULATED" /> {adapt.robustness_class || "n/a"}
          </div>
          <p className="mt-2 text-xs text-soc-muted">{adapt.explanation}</p>
        </section>
        <section className="rounded-lg border border-soc-border p-3 text-sm">
          <div className="text-[10px] uppercase text-soc-muted">What was learned?</div>
          <div className="mt-1 flex items-center gap-2">
            <KindBadge kind="HISTORICAL" /> {learn.label}
          </div>
          <p className="mt-2 text-xs text-soc-muted">{learn.explanation}</p>
        </section>
        <section className="rounded-lg border border-soc-border p-3 text-sm">
          <div className="text-[10px] uppercase text-soc-muted">Playbook evolution</div>
          <p className="mt-2 text-xs text-soc-muted">{play.explanation}</p>
        </section>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <section>
          <div className="text-[10px] uppercase text-soc-muted">What remains uncertain?</div>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
            {uncertainty.map((u) => (
              <li key={u}>{u}</li>
            ))}
          </ul>
        </section>
        <section>
          <div className="text-[10px] uppercase text-soc-muted">Investigation questions</div>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
            {questions.map((q) => (
              <li key={q}>{q}</li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
