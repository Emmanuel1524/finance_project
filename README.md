# Backtest WDO — Robô de abertura (EA v1.35)

Backtest/replay bar-by-bar, em Python, do EA MQL5 de abertura do WDO (mini dólar, B3) sobre candles M5. Premissas conservadoras (OHLC, política intrabar `adverse`). Objetivo de longo prazo: estratégia produtizável, sólida e escalável.

## Estrutura do repositório

```
├── src/wdo/                  # código reutilizável (pacote instalável)
│   ├── config.py             #   Config (parâmetros), round_tick
│   ├── data.py               #   loaders, validação, série contínua/rollover
│   ├── indicators.py         #   RSI e EMAs H1/D1 (candles fechados, point-in-time)
│   ├── strategies/           #   contrato Strategy + Baseline V0 (regras do EA)
│   ├── engine.py             #   simulador (execução, gaps, custos), ENGINE_VERSION, run_backtest
│   ├── partitions.py         #   partições de dados e guarda de acesso (pesquisa/validação/holdout)
│   ├── metrics.py            #   métricas de desempenho
│   └── reporting.py          #   relatório textual e gráficos
├── tests/                    # pytest
├── notebooks/                # pesquisa, validação e relatório (sem lógica de negócio)
├── configs/wdo_default.toml  # cenário base (custos provisórios) + partições de dados
├── data/raw/                 # dados brutos imutáveis (wdo_data.csv, export MT5 M5)
├── data/processed/           # dados derivados (gerado, fora do git)
├── reference/mt5/            # código-fonte MQL5 do EA: fonte da verdade das regras
├── experiments/              # registro versionado da pesquisa: uma run por prompt-task + leaderboard top 3
├── docs/agentic_documentation/  # contexto e práticas para agentes e humanos
├── outputs/                  # gerado: notebooks executados, figuras, runs (fora do git)
├── environment.yml           # ambiente conda `wdo-backtest`
├── pyproject.toml            # metadados do pacote + configuração do pytest
├── CLAUDE.md  AGENTS.md      # diretrizes para agentes (Claude Code / Codex)
```

## Setup e execução

Use o ambiente conda **`wdo-backtest`** (o `.venv` antigo está obsoleto):

```powershell
conda env create -f environment.yml     # só na primeira vez (instala também o pacote `wdo` em modo editável)
conda activate wdo-backtest
pytest -q
jupyter notebook notebooks/01_wdo_opening_backtest.ipynb   # kernel "Python (wdo-backtest)"
```

Se o kernel não aparecer: `python -m ipykernel install --user --name wdo-backtest --display-name "Python (wdo-backtest)"`.
Em um ambiente já existente, instale o pacote com `pip install -e .`.

Uso programático:

```python
from wdo import Config, Partitions, load_partition_bars, run_partition_backtest, print_backtest_report

config = Config.from_toml("configs/wdo_default.toml")
parts = Partitions.from_toml("configs/wdo_default.toml")
bars, _, _ = load_partition_bars("data/raw/wdo_data.csv", parts, "research", timezone=config.timezone)
results = run_partition_backtest(bars, parts, "research", config)   # validação/holdout exigem authorized=True
print_backtest_report(results)
```

## Dados esperados

Cada fonte M5 deve ter `datetime`, `open`, `high`, `low`, `close`, `volume` e timestamps em `America/Sao_Paulo` ou com offset explícito (`load_mt5_export` converte o export bruto do MT5). Para série contínua, entregue candles por vencimento com `contract` e uma tabela de rollover com `contract`, `start`, `end`. A construção falha em sobreposição, ausência de cobertura, duplicidade e OHLC inválido.

## Premissas

O cenário padrão é OHLC conservador. Ele não reproduz ticks, bid/ask nem EMAs H1/D1 em formação exatamente como o MT5. Ajuste explicitamente `point_value_brl`, custos e slippage (em `configs/`) antes de analisar o resultado financeiro.

Documentação para agentes e riscos conhecidos: [docs/agentic_documentation/README.md](docs/agentic_documentation/README.md).
