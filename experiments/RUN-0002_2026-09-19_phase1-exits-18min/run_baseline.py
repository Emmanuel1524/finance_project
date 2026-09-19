import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools

if __name__ == "__main__":
    d = tools.RUN / "EXP-0000_baseline-v0"
    d.mkdir(exist_ok=True)
    (d / "hypothesis.md").write_text("# EXP-0000 — Baseline V0 (RUN-0002)\n\nComparador fixo; re-executado no motor 1.1.0 e verificado idêntico ao EXP-0000 da RUN-0001. "
                                     "Não conta como tentativa.\n", encoding="utf-8")
    result = tools.run_strategy()
    m = tools.finish_experiment(d, result, {"strategy": "baseline_v0"})
    old = pd.read_csv(tools.ROOT / "experiments" / "RUN-0001_2026-09-19_phase1-first-18min" / "EXP-0000_baseline-v0" / "trades.csv")
    new = result.trades.reset_index(drop=True)
    cols = ["entry_datetime", "side", "entry_price", "exit_datetime", "exit_price", "net_pnl"]
    same = len(old) == len(new) and all((old[c].astype(str).to_numpy() == new[c].astype(str).to_numpy()).all() for c in cols)
    assert same, "V0 sob o motor 1.1.0 difere do EXP-0000 da RUN-0001"
    tools.write_decision(d, "# EXP-0000 — Baseline V0 (comparador)\n\nVerificação: trades idênticos aos da RUN-0001 (motor 1.0.0 → 1.1.0).\n")
    tools.add_registry(tools.registry_row2("EXP-0000", "", "baseline", "V0", "Baseline V0", "-", "BASELINE", m, "-", "-", "-", "-", 0))
    print("V0 IDÊNTICO ao da RUN-0001:", same, "| motor", result.engine_version)
    print(tools.line(m))
