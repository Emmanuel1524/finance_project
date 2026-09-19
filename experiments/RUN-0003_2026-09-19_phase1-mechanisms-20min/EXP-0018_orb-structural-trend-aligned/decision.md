# EXP-0018 — decisão: REJECT (NÃO SUSTENTADO; piorou)
Resultado: PF 0.612, WR 13.7%, PnL -R$1867, DD 23.0%, 51 trades, payoff 3.85, expectância -R$36.6, meses + 1/5, top5 86%. LONG -R$227 / SHORT -R$1640.
Placebo (20 sorteios): média -R$41.4; excesso +R$4.8 (1 EP ≈ R$11+: ruído). Placebo de SELEÇÃO: P(acaso >= candidato) = 93% (PnL) e 90% (PF): o filtro escolheu trades PIORES que quase todos os subconjuntos aleatórios.
Integrity: Look-ahead PASS (EMAs D1 fechadas na abertura) | Point-in-time PASS | Replay unchanged YES | New leakage risk NO | Leakage tests: auto-descoberta PASS
Overfitting: hipótese estrutural YES (mecanismo, independente); micro-tuning NO; complexidade justificada NO; estabilidade checada YES (1/5); concentração aceitável NO; validação consultada NO; premissa desafiada YES; placebo reportado YES
Lição: o alinhamento com a tendência D1 (reaberto agora para continuação) também não sustenta; o EXP-0004 (fades) e este (continuação) convergem: a tendência D1 não é um filtro útil nesta amostra.
