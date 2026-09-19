import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools

d = tools.RUN / "EXP-0000_baseline-v0"
(d / "hypothesis.md").write_text("# EXP-0000 — Baseline V0\n\nEstratégia original (EA v1.35 replicado, `strategies/baseline_v0.py`). Comparador fixo; "
                                 "não conta como tentativa de pesquisa.\n", encoding="utf-8")
result = tools.run_strategy()
m = tools.finish_experiment(d, result, {"strategy": "baseline_v0"})
tools.write_decision(d, "# EXP-0000 — Baseline V0 (comparador)\n\nDecisão: n/a (baseline). Portões D3 aplicados só para referência: "
                     f"{json.dumps(m['gates'])}. Integridade: motor 1.0.0 congelado; 45 testes passando.\n")
tools.add_registry(tools.registry_row("EXP-0000", "", "baseline", "V0", "Baseline V0", "-", "BASELINE", m))
print(tools.line(m))
for k in ("max_drawdown_pct", "months_positive", "monthly_pnl", "rolling20_min", "rolling20_pos_frac", "top5_trades_share", "top5_days_share",
          "max_month_share", "max_consec_losses", "max_days_underwater", "worst_trade", "entry_bar_exits", "by_side", "by_entry",
          "regime_vol_high_next", "regime_up_next", "gates", "gates_pass"):
    print(k, "=", json.dumps(m.get(k), ensure_ascii=False))
