# EXP-0020 — decisão: REJECT (NÃO SUSTENTADO; = acaso)
Resultado: PF 0.724, WR 15.2%, PnL -R$1359, DD 20.81% (reprova), 92 trades, payoff 4.03, expectância -R$14.77, meses + 1/5, top5 68.3%, 23 stops na própria barra de entrada.
Placebo (20 sorteios, mesma saída): média -R$14.59, p95 +R$1.6; excesso -R$0.18: indistinguível do acaso.
Integrity: Look-ahead PASS (barra 09:30 ET fechada; DST por tz_convert) | Point-in-time PASS | Replay unchanged YES (janela 09:00-12:00 é Config do candidato) | New leakage risk NO | Leakage tests: auto-descoberta PASS (leakage_config end 12:00)
Overfitting: hipótese estrutural YES (literatura de sazonalidade intradiária + mecanismo; independente da amostra); micro-tuning NO; complexidade justificada YES (0 dof); estabilidade checada YES (1/5); concentração aceitável NO (68%); validação consultada NO; premissa desafiada YES (janela livre, D9); placebo reportado YES
Lição: a informação de direção medida na Análise B parece específica da abertura da B3; a barra das 09:30 ET não a repete.
