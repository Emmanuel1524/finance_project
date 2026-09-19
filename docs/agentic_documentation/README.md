# agentic_documentation — índice

Documentação para **agentes de IA** (Claude Code, Codex e outros) e humanos entenderem este projeto rapidamente e trabalharem com o mesmo padrão de rigor.

Data de referência do snapshot: 2026-09-18. Tudo aqui foi escrito **lendo o código e os arquivos**; nenhum teste, backtest ou notebook foi executado ao criar esta documentação. Onde algo é inferência, está marcado como **[não verificado]**.

## ⚠️ Ambiente de execução (obrigatório)

**Todo código, teste e notebook deste projeto deve rodar no ambiente conda `wdo-backtest`** (definido em [`../../environment.yml`](../../environment.yml): Python 3.12, pandas 3.0, numpy, matplotlib, jupyter, ipykernel, nbconvert, pytest). O `.venv` antigo (Python 3.14) está **obsoleto — não use**.

- **Notebook (VS Code/Jupyter):** selecione o kernel **"Python (wdo-backtest)"** (`notebooks/01_wdo_opening_backtest.ipynb` já vem apontando para ele; o pacote `wdo` é instalado em modo editável pelo `environment.yml`).
- **Terminal (PowerShell):**
  ```powershell
  conda activate wdo-backtest      # se o conda não estiver no PATH: & "$env:USERPROFILE\miniconda3\Scripts\activate.ps1"
  pytest -q
  ```
- **Executar o notebook headless (sem abrir Jupyter)** — chame o `nbconvert` do próprio ambiente, senão o `jupyter` do PATH pode ser o do `.venv` e o kernel morre:
  ```bash
  E=/c/Users/EmmanuelSilv_41llm/miniconda3/envs/wdo-backtest
  export PATH="$E:$E/Scripts:$E/Library/bin:$PATH"; unset VIRTUAL_ENV
  python -m nbconvert --to notebook --execute notebooks/01_wdo_opening_backtest.ipynb \
      --ExecutePreprocessor.kernel_name=wdo-backtest --output-dir outputs/notebooks
  ```
- **Recriar o ambiente (nova máquina):** `conda env create -f environment.yml` e depois `python -m ipykernel install --user --name wdo-backtest --display-name "Python (wdo-backtest)"`. A primeira criação leva alguns minutos (aceita os Termos de Serviço dos canais do conda automaticamente).
- Novas dependências: adicionar em `environment.yml` (e em `pyproject.toml` se o pacote `wdo` depender delas) **com aprovação do usuário**.
- Em ambiente já existente, `pip install -e .` (na raiz) registra o pacote `wdo`.

Verificado em 2026-09-19 (motor 1.0.0): `pytest -q` → 45 passed; `notebooks/01_wdo_opening_backtest.ipynb` executa de ponta a ponta sem erros neste ambiente.

## Ordem de leitura

| # | Arquivo | Para quê |
|---|---|---|
| 1 | [01_project_overview.md](01_project_overview.md) | O que é o projeto, o que existe, estado atual |
| 2 | [02_strategy_spec.md](02_strategy_spec.md) | Regras da estratégia (EA MQL5) e como o Python as implementa |
| 3 | [03_architecture_and_code_map.md](03_architecture_and_code_map.md) | Mapa do código, fluxo de dados, contratos |
| 4 | [04_backtesting_best_practices.md](04_backtesting_best_practices.md) | Práticas de backtest rigoroso, vieses, validação |
| 5 | [05_replay_trading_guide.md](05_replay_trading_guide.md) | Simulação, integridade temporal (anti look-ahead), testes de vazamento, congelamento do motor |
| 6 | [06_quant_finance_playbook.md](06_quant_finance_playbook.md) | Metodologia quant: fases, framework de qualidade, robustez, política de dados, overfitting |
| 7 | [07_agent_protocol.md](07_agent_protocol.md) | Comportamento do agente: ciclo autônomo, registro de experimentos, orçamento, handoff |
| 8 | [08_roadmap_and_open_questions.md](08_roadmap_and_open_questions.md) | Riscos, portões G0–G3, Fase 1/2, decisões pendentes D1–D7 |
| 9 | [glossary.md](glossary.md) | Termos (PDH/PDL, IFR, tick, rollover, etc.) |

Regras curtas de conduta estão em `../../CLAUDE.md` e `../../AGENTS.md`.

## Se você só tem 2 minutos

- O projeto **replica em Python um robô MQL5 (EA v1.35) de abertura do WDO** (mini dólar, B3) para backtestar sobre candles M5.
- A **fonte da verdade das regras é o arquivo `reference/mt5/Robo_Abertura_WDO_Genial_v1.35.mq5`** (código MQL5). O Python (`src/wdo/`) deve espelhá-lo.
- Um backtest de diagnóstico do pipeline já rodou, mas seus números **não são referência de pesquisa** (ver 08). Antes de confiar em qualquer número: rode `pytest -q` e leia [08](08_roadmap_and_open_questions.md), que lista **divergências e riscos de look-ahead** já identificados.
- **Pesquisa de estratégia (Fase 1) NÃO está autorizada** até o usuário aprovar a metodologia e as decisões D1–D7 (08). Metodologia: [06](06_quant_finance_playbook.md) (fases, qualidade, dados, salvaguardas), [07](07_agent_protocol.md) (ciclo, registro, orçamento), [05 §10](05_replay_trading_guide.md) (integridade e congelamento do motor).
- Objetivo de longo prazo: estratégia **produtizável, sólida e escalável**. Rigor > velocidade.
