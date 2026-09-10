# API

Base URL: `http://127.0.0.1:8000`

All security results are **simulated**.

## Simulation

- `GET /api/simulation/state`
- `POST /api/simulation/start` `{ "scenario_id": "SCN-001" }`
- `POST /api/simulation/next-event`
- `POST /api/simulation/reset`
- `GET /api/simulation/scenarios`

## Core reads

- `GET /api/incidents`
- `GET /api/incidents/{id}`
- `GET /api/events`
- `GET /api/assets`
- `GET /api/attack-graph`
- `GET /api/predictions`

## Defense

- `POST /api/defense/recommend`
- `POST /api/defense/approve`
- `POST /api/defense/simulate`

## Replay and analysis

- `POST /api/replay`
- `POST /api/counterfactual/run`
- `POST /api/robustness/test`
- `POST /api/robustness/drop-event`
- `POST /api/intervention`

## Learning

- `POST /api/playbook/propose`
- `POST /api/playbook/approve`
- `GET /api/playbooks`
- `GET /api/playbooks/yaml`
- `GET /api/memory`
- `GET /api/audit`
- `GET /api/evaluation`
- `POST /api/ai/investigate`
- `POST /api/demo`

## WebSocket

- `ws://127.0.0.1:8000/ws/events`
