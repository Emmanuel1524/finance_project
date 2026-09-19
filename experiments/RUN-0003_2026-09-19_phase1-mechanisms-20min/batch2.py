import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from wdo.strategies.candidates_run3 import OrbNyOpen, OrbStructuralPdhTarget

R2 = tools.ROOT / "experiments" / "RUN-0002_2026-09-19_phase1-exits-18min"

if __name__ == "__main__":
    parent = tools.load_metrics(next(R2.glob("EXP-0011_*")) / "metrics.json")
    cfg_ny = replace(tools.CFG, start_hour=9, start_minute=0, end_hour=12, end_minute=0)
    tools.run_registered("EXP-0020_orb-ny-open", OrbNyOpen,
                         {"strategy": "OrbNyOpen", "signal": "5-min bar at 09:30 ET", "exit": "opposite extreme, no target, 17:55", "session_window": "09:00-12:00", "dof": 0},
                         parent, cfg=cfg_ny)
    tools.run_registered("EXP-0021_orb-structural-pdh-target", OrbStructuralPdhTarget,
                         {"strategy": "OrbStructuralPdhTarget", "target": "PDH/PDL if >= 2 pts away, else none", "dof": 0}, parent)
