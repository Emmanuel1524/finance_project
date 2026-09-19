import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from wdo.strategies.candidates_run3 import OrbStructuralRelVolume, OrbStructuralSecondEntry, OrbStructuralTrendAligned

R2 = tools.ROOT / "experiments" / "RUN-0002_2026-09-19_phase1-exits-18min"

if __name__ == "__main__":
    parent = tools.load_metrics(next(R2.glob("EXP-0011_*")) / "metrics.json")
    base_csv = next(R2.glob("EXP-0011_*")) / "trades.csv"
    print("REFERÊNCIA EXP-0012 (RUN-0002):", tools.line(tools.load_metrics(next(R2.glob("EXP-0012_*")) / "metrics.json")))
    tools.run_registered("EXP-0017_orb-structural-relvolume", OrbStructuralRelVolume,
                         {"strategy": "OrbStructuralRelVolume", "filter": "first-bar volume > median of previous 20", "dof": 0}, parent, base_trades_csv=base_csv)
    tools.run_registered("EXP-0018_orb-structural-trend-aligned", OrbStructuralTrendAligned,
                         {"strategy": "OrbStructuralTrendAligned", "filter": "D1 trend alignment", "dof": 0}, parent, base_trades_csv=base_csv)
    cfg2 = replace(tools.CFG, max_trades_per_day=2)
    tools.run_registered("EXP-0019_orb-structural-second-entry", OrbStructuralSecondEntry,
                         {"strategy": "OrbStructuralSecondEntry", "max_trades_per_day": 2, "dof": 0}, parent, cfg=cfg2)
