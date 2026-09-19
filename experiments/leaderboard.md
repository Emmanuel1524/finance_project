# Leaderboard — top 3 experimentos (sobrevivência)

Placar **global** (entre runs). Regras de comparação e de entrada/saída: `docs/agentic_documentation/06_quant_finance_playbook.md` §5 e `07_agent_protocol.md` §5. Apenas experimentos que passam nos portões (integridade limpa, revisão de overfitting limpa, não frágil, amostra suficiente) podem entrar. Julgado no **conjunto de pesquisa**; o top 3 de uma run é o que pode ser levado à validação, dentro do limite de consultas.

**Status (RUN-0001, 2026-09-19): vazio — nenhum candidato passou nos portões D3** (melhor frontier não-aprovado: RUN-0001/EXP-0005). **RUN-0002:** continua vazio; fronteira não-aprovada: RUN-0002/EXP-0012 (falha top-5 = 72% e concentração mensal; data-informed).

## Top 3 atual

| Posição | Experimento (RUN/EXP) | Pai | Resumo da hipótese | Por que está aqui (vs. V0 e vs. os demais) |
|---|---|---|---|---|
| 1 | — | — | — | — |
| 2 | — | — | — | — |
| 3 | — | — | — | — |

## Histórico (append-only)

| Data | Run/Exp | Evento (ENTROU / SAIU / NÃO ENTROU) | Substituiu | Motivo (comparação dimensão a dimensão) |
|---|---|---|---|---|
| 2026-09-19 | RUN-0001/EXP-0001..0008 | NÃO ENTROU | — | Todos reprovam em ao menos um portão (expectância > 0 após custos; 8 experimentos). Ver `RUN-0001/run_report.md`. |
| 2026-09-19 | RUN-0002/EXP-0009..0016 | NÃO ENTROU | — | Nenhum passa em todos os portões (EXP-0012 é o melhor, mas falha top-5 e concentração mensal). Ver `RUN-0002/run_report.md`. |
