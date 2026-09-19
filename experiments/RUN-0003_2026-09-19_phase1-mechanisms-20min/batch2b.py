import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from wdo.strategies.candidates_run3 import OrbStructuralPdhTarget

R2 = tools.ROOT / "experiments" / "RUN-0002_2026-09-19_phase1-exits-18min"

if __name__ == "__main__":
    parent = tools.load_metrics(next(R2.glob("EXP-0011_*")) / "metrics.json")
    tools.run_registered("EXP-0021_orb-structural-pdh-target", OrbStructuralPdhTarget,
                         {"strategy": "OrbStructuralPdhTarget", "target": "PDH/PDL if >= 2 pts away, else none", "dof": 0}, parent)
