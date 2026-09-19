# RUN-0002 — Phase 1, arquitetura de saída, janelas livres e controles (18 min)

- Prompt-task: Run 2 (ver o prompt do usuário na conversa; base: docs/agentic_documentation/, experiments/knowledge.md, RUN-0001). Orçamento **18 min**.
- Início 2026-09-19 02:18:51 | Prazo 02:36:51 | Experimentos encerrados 02:27:29 | Relatório 02:29:47
- Commit-base: 63603d1 (motor 1.1.0; a árvore tinha só os documentos de metodologia/knowledge pendentes, incluídos no commit final) | ENGINE_VERSION 1.1.0 | pytest 77 passed na partida
- Dados: partição de PESQUISA 2026-01-02 → 2026-06-30 via `wdo.partitions` (nunca authorized=True); validação e holdout NÃO acessados
- Config-base: `configs/wdo_default.toml` (custos provisórios D6); candidatos com janela livre usam Config próprio (registrado em strategy_config.json)
- Experimentos: 8 (EXP-0009..0016) + baseline EXP-0000 (idêntico ao da RUN-0001 sob o motor 1.1.0). Tentativas cumulativas sobre a partição: 8 + 8 = **16**
- Placebo: 10 sorteios (sementes 1000..1009), processos em paralelo (8 CPUs), ~5–10 s por experimento
- Alterações de código: novos `src/wdo/strategies/candidates_run2.py` e `tests/test_candidates_run2_leakage.py`, exports em `strategies/__init__.py`; motor, V0, testes existentes, notebook e artefatos da RUN-0001 intocados
