# RansomGuard-X

Adaptive Ransomware Defense & Cyber Decision Intelligence prototype for a **synthetic** SOC lab (RMK College Cyber Defense Center, fictional).

This is a hackathon demonstration system. It is **not production-ready** and does **not** prevent real ransomware.

## Overview

RansomGuard-X walks an analyst through a closed decision loop:

**DETECT → UNDERSTAND → PREDICT → SIMULATE → RESPOND → LEARN → EVOLVE → EVALUATE**

All attacks, defenses, and measurements are **synthetic simulation**. Human approval is required before simulated containment. Playbook changes are evidence-backed **proposals** and are never auto-approved.

## Architecture

- **Frontend:** React + Vite + Tailwind (Command Center and supporting pages)
- **Backend:** FastAPI + SQLite
- **Live updates:** WebSocket `ws://127.0.0.1:8000/ws/events`
- **Engines:** detection, attack graph, prediction, defense, containment (simulated), forks (read-only), adaptation, learning, playbook evolution, investigator, evaluation

The backend is the source of truth. The UI does not invent security state.

## How to run

Backend (from `backend/`):

```powershell
.\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend (from `frontend/`):

```powershell
npm run dev
```

Open `http://localhost:5173`. The Vite proxy forwards `/api` and `/ws` to port 8000.

No external LLM, internet, credentials, or real network traffic are required for the demo.

## Safe simulation

- **Run Safe Simulation** starts SCN-001 (progressive synthetic ransomware-prep path).
- **Next Event** advances one catalog event deterministically.
- **Reset Simulation** clears the current incident, open prediction, and live events. It does **not** erase prediction/learning memory, defense memory, playbook versions, or evaluation reports.

Nothing scans real networks, encrypts files, isolates machines, or changes firewalls.

## Main demo workflow (SCN-001)

1. Suspicious process on LAB-PC-21  
2. Mass file modification  
3. Rapid file rename  
4. Credential access  
5. Privilege escalation  
6. Lateral movement to FAC-PC-07  
7. File server access (FILE-SRV-01)  
8. Backup access attempt (BACKUP-SRV-01)

Along the path: risk and evidence, observed attack graph, next-target **prediction** (not observed reality), defense recommendation, **human review**, **simulated containment**, simulated adaptation, learning from prediction vs reality, playbook **proposal**, AI investigator explanation, synthetic evaluation.

## Modules

1. Behavioral detection and evidence correlation  
2. Attack graph (observed path only)  
3. Next-target prediction  
4. Adaptive defense recommendation  
5. Human approval  
6. Simulated containment  
7. Attack Fork Lab (read-only futures)  
8. Simulated attacker adaptation / robustness  
9. Prediction → reality learning  
10. Playbook evolution (human-approved versions)  
11. AI investigator (explanation only)  
12. Evaluation & benchmarks (synthetic metrics)

## API (selected)

- `GET /api/health`
- `GET /api/detection/current`
- `GET /api/attack-graph`
- `GET /api/predictions`
- `GET /api/defense/recommend`
- `POST /api/defense/review` · `/approve` · `/reject`
- `GET /api/forks` and `GET /api/simulation/forks`
- `GET /api/adaptation`
- `GET /api/learning/summary` · `/history` · `/defense-memory`
- `GET /api/playbooks` · `/current` · `/proposals`
- `POST /api/playbooks/proposals/{id}/approve` · `/reject`
- `GET /api/investigator`
- `GET /api/evaluation` · `POST /api/evaluation/run`
- WebSocket `/ws/events`

## Evaluation

Evaluation runs isolated synthetic scenarios (SCN-001–006). Metrics are computed from those runs. Insufficient data is reported as `NOT_ENOUGH_DATA`. SCN-003/SCN-004 may be false negatives under current detection correlation — that result is left honest, not tuned away.

Label: **SYNTHETIC EVALUATION**. Not production accuracy.

## Limitations

- Synthetic scenarios and deterministic scoring  
- Limited scenario diversity  
- No production telemetry  
- No real ransomware, credentials, or network activity  
- In-process learning/playbook memory (survives simulation reset, not process restart)  
- Optional LLM is off by default; demo does not depend on it  

## Safety

The system must not scan real networks, execute ransomware, encrypt or modify real files, access credentials, disable accounts, isolate machines, change firewalls, or generate attack commands. Playbook YAML is documentation only and is not executed.
