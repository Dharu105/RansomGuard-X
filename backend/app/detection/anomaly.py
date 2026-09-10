"""Isolation Forest helpers — re-export Phase 2 model API."""
from app.detection.models import score_events, train_and_persist

__all__ = ["score_events", "train_and_persist"]
