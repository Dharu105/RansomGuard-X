# Architecture

RansomGuard-X is a **simulated** adaptive ransomware defense and cyber decision-intelligence prototype.

## Safety

- No real files are encrypted or modified.
- No real networks are scanned.
- All assets belong to the fictional **RMK College Cyber Defense Center**.
- Defense actions never touch a live environment.

## Closed loop

Observe → Detect → Understand → Predict → Choose defense → Contain → Reconstruct → Intervention window → Replay alternatives → Missed impact → Learn → Update playbook → Defend better.

## Layers

```
React (Vite)
  → REST + WebSocket
    → FastAPI
      → Simulation Engine (authoritative state)
        → Detection / Intent / Graph / Prediction
        → Defense / Counterfactual / Adaptation
        → Learning / Playbooks / Audit
      → SQLite (SQLAlchemy)
```

The frontend **never invents** security state. Every page reads `GET /api/simulation/state` and live `/ws/events` updates.

## ML

- Isolation Forest for anomaly scoring, with a deterministic weighted fallback.
- Deterministic target predictor, optionally blended with a Random Forest if a model file exists.
- Optional Gemini API for investigator explanations only. Decisions are never made by an LLM.
