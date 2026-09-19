import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from wdo.strategies.candidates_run2 import LateDayMomentumExit

D13 = """# EXP-0013 — decisão: REJECT (NÃO SUSTENTADO; abaixo do placebo)
Resultado: PF 0.86, WR 34.7%, PnL -R$1270, DD 25.98% (reprova), 75 trades, payoff 1.62, expectância -R$16.9, meses + 3/5, top5 47.7% (reprova), pior trade -R$367 (stop estrutural largo), SHORT -R$1371 vs LONG +R$101.
Placebo (10 sorteios): média -R$8.97, p95 +R$18.9, máx +R$23.7: o candidato fica ABAIXO da média do acaso (excesso -R$8/trade): o rompimento do range de 30 min não carrega direção útil com esta saída.
Integrity: Look-ahead PASS (range de barras fechadas; entrada na abertura seguinte) | Point-in-time PASS | Replay unchanged YES | New leakage risk NO | Leakage tests: pendente até o fim da run
Overfitting: hipótese estrutural YES (literatura); micro-tuning NO; complexidade justificada YES (0 dof); estabilidade checada YES; concentração aceitável NO; validação consultada NO; premissa desafiada YES; placebo reportado YES
Lição: o sinal do EXP-0011 é o corpo da 1ª barra de 5 min, não o rompimento do range de 30 min; famílias Range-Breakout-30: 1 rejeição.
"""

H = """# EXP-0014 — Momentum intradiário de fim de dia (Gao et al. 2018) com saída por horário
Pai: RUN-0001/EXP-0008 (INVÁLIDO/BLOCKED, reaberto). Ramo: Intraday-Momentum-LateDay. Família: momentum intradiário.
**hypothesis_source:** literatura (Gao, Han, Li, Zhou, JFE 2018: retorno da 1ª meia hora, medido do fechamento anterior, prevê o da última meia hora; mais forte em dias voláteis).
**Premissa desafiada:** que só se opere a abertura (janela 09:00–10:30) e que toda saída seja stop/alvo fixo; janela livre (D9).
**Reabertura:** (i) MECANISMO NOVO: `ExitSpec.exit_time` (motor 1.1.0). O EXP-0008 era BLOCKED (sem saída por horário; posições atravessavam a noite): nada foi concluído.
**Hipótese:** r1 = fechamento das 09:30 / fechamento anterior - 1; entrar às 17:30 na direção de r1 e sair às 17:55 captura a continuação da última meia hora.
**Os 4 pontos:** (i) a saída fixa do EXP-0008 deixava o trade atravessar a noite; (ii) stop = 0,25 × range do dia anterior (única alternativa a priori) e saída por horário 17:55; janela de sessão 09:00–18:00 (Config do candidato); (iii) hipótese antes intestável, não um vizinho; (iv) sustenta: expectância > 0 e acima do placebo com portões OK; rejeita: caso contrário.
Graus de liberdade: 1 (K). Premissas: pregão regular até 18:00 (o dado tem barras até 18:25).
"""

if __name__ == "__main__":
    tools.write_decision(tools.RUN / "EXP-0013_or30-breakout", D13)
    m13 = tools.load_metrics(tools.RUN / "EXP-0013_or30-breakout" / "metrics.json")
    tools.add_registry(tools.registry_row2("EXP-0013", "EXP-0000", "OR30-Breakout", "range-breakout", "30-min opening range breakout, structural stop, EOD exit",
                       "OpeningRange30Breakout", "REJECT", m13, "literatura+mecanismo", "fade entries and fixed 10/6 exits", "new family", 0, 5))
    cfg = replace(tools.CFG, start_hour=9, start_minute=0, end_hour=18, end_minute=0)
    tools.run_experiment2("EXP-0014", "late-day-momentum-exit", LateDayMomentumExit, H,
                          {"strategy": "LateDayMomentumExit", "k_range": 0.25, "entry": "17:30", "exit_time": "17:55", "session_window": "09:00-18:00", "dof": 1},
                          tools.load_metrics(tools.RUN / "EXP-0000_baseline-v0" / "metrics.json"), cfg=cfg)
