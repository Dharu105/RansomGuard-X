"""RansomGuard-X FastAPI entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.database import init_db
from app.detection.anomaly import train_and_persist
from app.prediction.engine import train_rf
from app.seed import seed_if_empty

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed_if_empty()
    try:
        train_and_persist()
    except Exception:
        pass
    try:
        train_rf()
    except Exception:
        pass
    yield


app = FastAPI(
    title="RansomGuard-X",
    description="Adaptive Ransomware Defense & Cyber Decision Intelligence Platform (SIMULATED)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

# WebSocket is registered on router as /ws/events but mounted under /api.
# Also expose canonical /ws/events as specified.
from fastapi import WebSocket, WebSocketDisconnect
from app.simulation.engine import engine
from app.ws import hub


@app.websocket("/ws/events")
async def ws_root(ws: WebSocket):
    await hub.connect(ws)
    await ws.send_json({"type": "hello", "state": engine.snapshot()})
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(ws)


@app.get("/")
def root():
    return {
        "name": "RansomGuard-X",
        "tagline": "Detect. Predict. Decide. Defend. Replay. Learn.",
        "simulated": True,
        "docs": "/docs",
    }
