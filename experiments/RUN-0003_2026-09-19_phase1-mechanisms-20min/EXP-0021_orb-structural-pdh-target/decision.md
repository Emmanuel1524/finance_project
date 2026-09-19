# EXP-0021 — decisão: REJECT (NÃO SUSTENTADO; destrói o resultado do pai)
Resultado: PF 0.589, WR 23.0%, PnL -R$3030, DD 31.73% (reprova), 100 trades, payoff 1.97, expectância -R$30.3, meses + 1/5; 17 TAKE_PROFIT no PDH/PDL. Pai EXP-0011: +R$0.4.
Placebo (20 sorteios): média -R$30.67; excesso +R$0.37: indistinguível do acaso. Limitar os ganhos ao extremo do dia anterior removeu os poucos vencedores grandes de que a arquitetura depende.
Nota de registro: a 1ª tentativa de rodar o placebo falhou por limitação do utilitário (alvo por nível não convertido em distância para a direção aleatória; o motor recusou a ExitSpec inválida); corrigi `tools.Recorder` e reexecutei; o resultado do candidato é o mesmo (determinístico).
Integrity: Look-ahead PASS (PDH/PDL do dia anterior na abertura; alvo validado >= 2 pts) | Point-in-time PASS | Replay unchanged YES | New leakage risk NO | Leakage tests: auto-descoberta PASS
Overfitting: hipótese estrutural YES (mecanismo; independente); micro-tuning NO (margem de 2 pts é guarda de validade); complexidade justificada NO; estabilidade checada YES (1/5); concentração aceitável NO; validação consultada NO; premissa desafiada YES (ausência de alvo); placebo reportado YES
Lição: alvo (fixo, EXP-0002/0003; ou estrutural, este) reduz o resultado da arquitetura: não capar os vencedores.
