"""Estratégias: contrato em `base.py`, regras do Baseline V0 em `baseline_v0.py`."""
from .base import BarOpen, ExitSpec, OrderIntent, SessionDecision, SessionOpen, Strategy
from .baseline_v0 import BaselineV0
from .candidates import LateDayMomentum, OpeningMomentum, OutsideRangeFade, V0NoChannel, V0NoChannelVolGate, V0TrendAligned, V0VolGate

__all__ = ["BarOpen", "ExitSpec", "OrderIntent", "SessionDecision", "SessionOpen", "Strategy", "BaselineV0", "V0VolGate", "OpeningMomentum", "V0TrendAligned", "V0NoChannel", "V0NoChannelVolGate", "OutsideRangeFade", "LateDayMomentum"]
