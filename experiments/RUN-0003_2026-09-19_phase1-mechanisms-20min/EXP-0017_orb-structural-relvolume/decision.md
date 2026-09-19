# EXP-0017 — decisão: REJECT (NÃO SUSTENTADO; o filtro escolheu trades piores que o típico)
Resultado: PF 0.856, WR 23.3%, PnL -R$546, DD 21.4%, 43 trades, payoff 2.83, expectância -R$12.7, meses + 2/5, top5 79%. Pai EXP-0011: exp. +R$0.4.
Placebo (20 sorteios, direção aleatória, mesma saída): média -R$34.2, p95 +R$8.35; excesso +R$21.5 (a arquitetura perde muito com direção aleatória; irrelevante para a comparação com o pai).
Placebo de SELEÇÃO (20.000 subconjuntos de 43 dos 100 trades do EXP-0011): P(acaso >= candidato) = 66% no PnL médio e 65% no PF => o filtro de volume relativo NÃO selecionou trades melhores que o acaso (mediana do acaso ≈ 0; candidato -12.7).
Integrity: Look-ahead PASS (volume da 1ª barra já fechada; mediana de sessões passadas) | Point-in-time PASS | Replay unchanged YES | New leakage risk NO | Leakage tests: auto-descoberta PASS (tests/test_candidates_auto_leakage.py)
Overfitting: hipótese estrutural YES (literatura+mecanismo, independente da amostra); micro-tuning NO (janela 20 e histórico 10 reusam o D7); complexidade justificada NO (sem ganho); estabilidade checada YES (2/5); concentração aceitável NO (79%, mas ver achado sobre o portão de concentração); validação consultada NO; premissa desafiada YES; placebo reportado YES
Lição: o mecanismo "in play" da literatura (ações/ETFs dos EUA) não se transfere ao WDO nesta amostra.
