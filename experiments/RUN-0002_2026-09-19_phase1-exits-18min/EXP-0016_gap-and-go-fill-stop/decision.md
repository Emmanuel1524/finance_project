# EXP-0016 — decisão: REJECT (NÃO SUSTENTADO; direção do gap pior que o acaso com esta saída)
Resultado: PF 0.72, WR 26.1%, PnL -R$2451, DD 30.7% (reprova), 88 trades, payoff 2.04, expectância -R$27.85, meses + 1/5, pior trade -R$547.
Placebo (10 sorteios com o MESMO stop): média -R$0.17, p95 +R$23.9, máx +R$34.0: candidato MUITO abaixo (excesso -R$27.7/trade): a direção do gap não é informativa a favor, e o resultado sugere direção inversa.
NÃO se inverte a direção só porque perdeu (resultado -> explicação é proibido): um fade de gap com invalidação estrutural é uma hipótese NOVA que exigiria mecanismo próprio e novo teste.
Integrity: Look-ahead PASS (abertura vs fechamento da sessão anterior) | Point-in-time PASS | Replay unchanged YES (janela 09:00-18:00 é Config do candidato) | New leakage risk NO | Leakage tests: ver run_report
Overfitting: hipótese estrutural YES; micro-tuning NO (guarda técnica |gap|>=2); complexidade justificada YES (0 dof); estabilidade checada YES (1/5 meses); concentração aceitável NO (top5 44.9%); validação consultada NO; premissa desafiada YES; placebo reportado YES

## Atualização de integridade (fim da run)
Leakage tests (05 §11) executados: **PASS** (tests/test_candidates_run2_leakage.py, 9 passed).
