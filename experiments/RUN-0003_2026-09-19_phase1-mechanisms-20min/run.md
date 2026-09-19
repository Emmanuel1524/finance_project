# RUN-0003 — Phase 1: mecanismos independentes, placebo de seleção, lotes (X = 20 min de EXPERIMENTAÇÃO)

- Prompt-task: Run 3 (ver o prompt do usuário na conversa). Diretriz do relógio (07 §6): os 20 min valem só para experimentação; setup e fechamento ficam fora; limite brando; teto de 25 experimentos.
- **Tempos:** setup 03:14:36 → 03:16:32 (~1.9 min) | **experimentação 03:16:32 → 03:24:25 (~7.9 min de 20; encerrada antes do prazo porque não restou hipótese independente e não-tuning)** | fechamento iniciado 03:26:40 (duração no relatório)
- Commit-base: 5ab87c5 (motor 1.1.0); a árvore tinha os pendentes esperados (docs 05/06/07/08, knowledge.md, teste de vazamento automático), incluídos no commit final
- Dados: partição de PESQUISA 2026-01-02 → 2026-06-30 via `wdo.partitions` (nunca authorized=True); validação e holdout NÃO acessados
- Config-base: `configs/wdo_default.toml` (custos provisórios D6); candidatos com janela/limite próprios usam Config próprio (strategy_config.json)
- Experimentos: 5 tentativas (EXP-0017..0021) + 1 hipótese BLOCKED (EXP-0022, não conta) + baseline EXP-0000 (idêntico ao da RUN-0002). Tentativas cumulativas: 16 + 5 = **21**
- Análises (não são tentativas): A (placebo de seleção), B (placebo reforçado, 200 sorteios), C (deriva intradiária), D (sensibilidade de execução)
- Placebo: 20 sorteios por experimento (processos paralelos, ~9 s cada); Análise B com 200 sorteios (~46 s)
- Alterações de código: novos `src/wdo/strategies/candidates_run3.py` e o utilitário desta pasta; exports em `strategies/__init__.py`; motor, V0, testes existentes, notebook e artefatos das RUN-0001/0002 intocados
- **Fechamento:** 03:26:38 → 03:27:58 (~1.3 min) | **Total da run:** ~13.4 min | pytest completo: 94 passed
