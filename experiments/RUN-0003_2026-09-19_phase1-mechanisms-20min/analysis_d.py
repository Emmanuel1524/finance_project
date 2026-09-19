"""Análise D (não é tentativa): sensibilidade de EXECUÇÃO (slippage × custos) das arquiteturas da fronteira, partição de pesquisa.

Regra 06 §2/§6: sensibilidade de execução vale nas duas fases; aplica-se igualmente a todos os candidatos.
"""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from wdo.strategies.candidates_run2 import OrbStructuralStop, OrbStructuralVolGate

if __name__ == "__main__":
    rows = []
    for label, factory in (("EXP-0011 (ORB estrutural)", OrbStructuralStop), ("EXP-0012 (+ vol alta, data-informed)", OrbStructuralVolGate)):
        for slip in (0.0, 0.5, 1.0):
            for cost in (0.0, 1.0):                                  # R$ por contrato por lado (comissão+taxas)
                cfg = replace(tools.CFG, slippage_points=slip, commission_per_contract=cost * 0.8, fees_per_contract=cost * 0.2)
                res = tools.run_strategy(factory, cfg)
                t = res.trades
                pnl = t.net_pnl
                gp, gl = pnl[pnl > 0].sum(), -pnl[pnl < 0].sum()
                rows.append(f"| {label} | {slip} | {cost:.1f} | {len(t)} | {pnl.mean():+.1f} | {gp / gl:.2f} | {pnl.sum():+.0f} |")
    md = ("# Análise D — sensibilidade de execução (slippage × custos), partição de pesquisa\n\n"
          "| Arquitetura | Slippage (pt/lado) | Custo (R$/contrato/lado) | Trades | Expectância (R$) | PF | PnL (R$) |\n|---|---|---|---|---|---|---|\n"
          + "\n".join(rows) + "\n\nCenário base (D6 provisório): slippage 0,5 e custo 1,0. Leitura: a diferença entre a linha (0; 0) e o base mostra quanto do resultado é consumido pela execução.\n")
    (tools.RUN / "analysis_d.md").write_text(md, encoding="utf-8")
    print(md.encode("ascii", "replace").decode())
