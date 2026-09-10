# Demo

## Run

Backend (from `backend/`):

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (from `frontend/`):

```
npm install
npm run dev
```

Open `http://localhost:5173`.

## 3-minute demo

Use **Start 3-Minute Demo** on Command Center. It drives the same simulation state:

| Time | Phase |
| 0:00 | Safe environment |
| 0:20 | Suspicious activity |
| 0:40 | Ransomware confidence rises |
| 1:00 | Attack graph |
| 1:20 | Target prediction |
| 1:40 | Defense comparison |
| 2:00 | Human approval |
| 2:15 | Simulated containment |
| 2:30 | Incident replay |
| 2:40 | Alternate realities |
| 2:50 | Defense regret |
| 3:00 | Playbook evolved |

Optional: set `GEMINI_API_KEY` in `backend/.env` for LLM explanations. The app works without it.

## Disclaimer

RMK College Cyber Defense Center is fictional. Results are simulated/experimental and are not real-world protection claims.
