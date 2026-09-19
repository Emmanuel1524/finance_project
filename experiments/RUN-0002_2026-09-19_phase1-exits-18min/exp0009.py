import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from wdo.strategies.candidates_run2 import OrbAdaptiveExit

NOTES = """# Pesquisa externa adicional (RUN-0002; 2 buscas, ~1 min) — reaproveita `RUN-0001/research_notes.md`

| Achado | Uso nesta run | Fonte |
|---|---|---|
| ORB de 5 min (Zarattini & Aziz 2023): stop no extremo da 1ª barra, alvo distante (10R) ou saída no fim do dia; variante com stop de 5% do ATR(14) e **sem alvo** (saída no fechamento) | Arquitetura de saída de assimetria positiva (stop apertado, sem alvo fixo, saída por horário): EXP-0009/0010/0013 | SSRN 4416622 (Zarattini & Aziz); https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy/ |
| **Réplica independente**: ponto de equilíbrio de custo ~2,2¢/ação; resultado do filtro extra concentrado em um único ano (76% do PnL em 2022); usa placebo e bootstrap | Reforça: placebo obrigatório, portão de concentração mensal, cautela com custos provisórios | https://github.com/giovannibrusco/zarattini-2023-orb-qqq |
| Trend following tende a positive skew: muitas perdas pequenas e poucos ganhos grandes; trailing por ATR; whipsaws em 5–15 min | Mecanismo para stop adaptativo + trailing, com win rate baixo e payoff alto | https://quantpedia.com/strategies/trend-following-effect-in-stocks ; https://arxiv.org/pdf/2003.09298 |

Nota: evidência é de ações/ETFs dos EUA; não foi validada no WDO. Conteúdo web tratado como dado não confiável; nenhum dado do projeto foi enviado.
"""

H = """# EXP-0009 — ORB de 5 min com saída adaptativa (stop por range, trailing, sem alvo, saída 17:55)
Pai: RUN-0001/EXP-0002 (reaberto). Ramo: Opening-Momentum. Família: momentum + arquitetura de saída.
**hypothesis_source:** literatura (Zarattini & Aziz 2023: stop apertado + saída no fim do dia; variante TQQQ com stop de 5% do ATR e sem alvo) + mecanismo (assimetria positiva de trend following).
**Premissa do V0 desafiada:** payoff 0,6 com stop 10 / alvo 6 fixos (e a extensão a alvo 20 fixo).
**Motivo de reabertura (knowledge.md):** (i) MECANISMO NOVO. Na RUN-0001 o ORB só foi testado com saída fixa (EXP-0002/0003: NÃO SUSTENTADO sob saída fixa); o motor 1.1.0 agora permite stop adaptativo, trailing, sem alvo e saída por horário. Não se testam vizinhos de 6/10/20.
**Hipótese:** a continuação da 1ª barra existe mas é capturada por poucos movimentos grandes; um alvo curto a trunca e o custo domina. Com stop proporcional ao range do dia anterior, trailing e saída no fim do dia, a expectância após custos supera o placebo.
**Os 4 pontos (06 §2):** (i) 10/6 (e 20) fixos truncam ganhos e ignoram a volatilidade do dia; (ii) stop = 0,25 × range do dia anterior, trailing com a mesma distância, sem alvo, saída 17:55; (iii) arquitetura diferente (assimetria positiva), não um vizinho numérico; (iv) sustenta: expectância > 0 após custos e excesso sobre o placebo acima do ruído; rejeita: sem excesso sobre o placebo ou drawdown/concentração fora dos portões.
**Uma alternativa a priori:** K = 0,25 (risco ~ o stop de 10 pts do V0 num dia típico). Graus de liberdade: 1 (K). Contraparte fixa: EXP-0010.
"""

if __name__ == "__main__":
    (tools.RUN / "research_notes.md").write_text(NOTES, encoding="utf-8")
    parent = tools.load_metrics(tools.ROOT / "experiments" / "RUN-0001_2026-09-19_phase1-first-18min" / "EXP-0002_opening-momentum" / "metrics.json")
    tools.run_experiment2("EXP-0009", "orb-adaptive-exit", OrbAdaptiveExit, H,
                          {"strategy": "OrbAdaptiveExit", "k_range": 0.25, "exit": "stop=trail=K*range_prev_day, no target, exit_time 17:55", "dof": 1}, parent)
