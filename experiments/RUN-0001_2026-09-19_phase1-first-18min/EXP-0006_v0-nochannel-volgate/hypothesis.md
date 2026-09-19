# EXP-0006 — V0 sem canal + só regime de volatilidade alta
Pai: EXP-0005. Ramo: V0-Filters. Família: composição de duas restrições estruturais independentes.
**Hipótese:** as duas restrições atacam causas distintas (P3: seleção adversa em zonas de stop-run; baixa vol: custo/stop fixos vs range pequeno);
combiná-las deve elevar a qualidade média dos trades restantes. Cada uma já foi testada isoladamente (EXP-0005, EXP-0001) com racional próprio.
**Critério de complexidade:** só vale se a combinação melhorar materialmente robustez (drawdown, estabilidade, expectância) sobre o melhor filtro isolado (ablação: comparar com EXP-0005 e EXP-0001);
com poucos trades (n ~ 30-40) o resultado será frágil.
**Mudança:** V0NoChannelVolGate = EXP-0001 + EXP-0005. Sem parâmetros novos.
