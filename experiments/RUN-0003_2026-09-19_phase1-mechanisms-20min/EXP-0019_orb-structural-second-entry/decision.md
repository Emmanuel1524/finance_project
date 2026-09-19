# EXP-0019 — decisão: REJECT (NÃO SUSTENTADO; piora drawdown e resultado)
Resultado: PF 0.905, WR 18.2%, PnL -R$987, DD 34.89% (reprova), 121 trades (100 iniciais + 21 re-entradas), payoff 4.07, expectância -R$8.16, meses + 3/5, 20 perdas seguidas.
As 21 re-entradas (ORB_STRUCT_RE): -R$1027, WR 14.3%. Os 100 primeiros trades reproduzem exatamente o EXP-0011 (+R$40).
Placebo (20 sorteios): média -R$16.96, p95 +R$3.1; excesso +R$8.8 (< 1 EP). Placebo de seleção: n/a (trades não são subconjunto da arquitetura-base).
Integrity: Look-ahead PASS (stop-out inferido só de barras fechadas, mesma regra do motor; re-entrada por fechamento de barra) | Point-in-time PASS | Replay unchanged YES (max_trades_per_day=2 é Config do candidato) | New leakage risk NO | Leakage tests: auto-descoberta PASS (leakage_config max_trades_per_day=2)
Overfitting: hipótese estrutural YES (mecanismo); micro-tuning NO; complexidade justificada NO; estabilidade checada YES; concentração aceitável NO; validação consultada NO; premissa desafiada YES (limite de 1 trade/dia, D9); placebo reportado YES
Lição: recuperação de rompimento falho não agrega; re-entrada correlaciona perdas no mesmo dia (não são amostras independentes). Família multi-trade: 1 rejeição.
