# RUN-0001 — Phase 1, primeiro teste de 18 minutos

- Prompt-task: descoberta de estratégia (Fase 1) conforme docs/agentic_documentation/ e o prompt de 15 min do usuário, com orçamento ajustado para **18 min** (D2 por tempo).
- Início: 2026-09-19 01:15:36 | Prazo: 01:33:36 | Encerramento dos experimentos: 01:24:49 | Relatório: 01:26:23
- Commit-base: 8f1ddf1 (G0, motor congelado) | ENGINE_VERSION 1.0.0 | pytest 45 passed na partida
- Dados: partição de PESQUISA 2026-01-02 → 2026-06-30 via `wdo.partitions` (nunca authorized=True); validação e holdout NÃO acessados; hash de `data/raw/wdo_data.csv` via git (commit-base)
- Config-base: `configs/wdo_default.toml` (custos provisórios D6: slippage 0,5 pt/lado, R$ 1,00/contrato/lado, ponto R$ 10; intrabar adverse; 1 trade/dia)
- Experimentos: 8 (EXP-0001..0008) + baseline EXP-0000 (não conta como tentativa). Nenhuma consulta à validação.
- Alterações de código: apenas novos arquivos (`strategies/candidates.py`, `tests/test_candidates_leakage.py`, esta pasta). Motor, V0, notebook e testes existentes intocados.
