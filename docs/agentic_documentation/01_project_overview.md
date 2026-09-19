# 01 — Visão geral do projeto

## Objetivo

1. **Curto prazo:** backtest auditável e conservador do robô "Robo Abertura WDO – Genial Investimentos" (EA MetaTrader 5, v1.35) sobre candles M5 do WDO.
2. **Longo prazo:** evoluir para uma estratégia **produtizável, sólida e escalável** (paper trading → produção, multi-ativo, monitoramento).

## Ativo e mercado

- **WDO**: mini contrato futuro de dólar comercial, B3 (Brasil). Tick = **0,5 ponto**. Valor por ponto usado como premissa: **R$ 10 / ponto / contrato** (configurável; confirmar com a B3/corretora antes de analisar PnL).
- Símbolo no MT5: `WDOFUT` (o MT5 da Genial faz crossorder automático para o contrato vigente `WDO`).
- Horário de operação da estratégia: **09:00 às 10:30 (Brasília)**, com leilão de abertura às 08:55.
- Timezone canônico do projeto: `America/Sao_Paulo`.

## Inventário de arquivos (snapshot 2026-09-18)

| Arquivo | Tamanho aprox. | O que é |
|---|---|---|
| `reference/mt5/Robo_Abertura_WDO_Genial_v1.35.mq5` | 40 KB | Código-fonte MQL5 do EA v1.35 (antes `mt5_bot`, sem extensão). **Referência das regras.** |
| `src/wdo/` | 9 módulos | Pacote Python: `config`, `data`, `indicators`, `strategies/` (contrato + V0), `engine` (simulador 1.1.0), `partitions`, `metrics`, `reporting` |
| `configs/wdo_default.toml` | — | Cenário padrão (`Config.from_toml`) |
| `pyproject.toml` | — | Pacote `wdo` (src layout, instalado com `pip install -e .`) + config do pytest |
| `tests/` | 6 arquivos | 77 testes pytest (regras, execução, indicadores, vazamento, partições, capacidade de saída, regressão do motor) |
| `experiments/` | — | Registro versionado da pesquisa (uma run por prompt-task) + leaderboard top 3 |
| `notebooks/01_wdo_opening_backtest.ipynb` | 10 KB | Notebook de execução/auditoria. Agora lê `data/raw/wdo_data.csv` com `load_mt5_export` e executa backtest, gráficos e reconciliação (células antes comentadas foram ativadas em 2026-09-18) |
| `environment.yml` | — | Ambiente conda `wdo-backtest` (obrigatório) |
| `data/raw/wdo_data.csv` | 1,3 MB | 18.900 linhas de candles M5, 2026-01-02 → 2026-09-01 (exportação MT5) |
| `README.md` | — | Estrutura do repositório, setup e uso |
| `outputs/` | — | Gerado (fora do git): notebooks executados, figuras, runs |
| `data/processed/` | — | Dados derivados (gerado, fora do git) |
| `CLAUDE.md` / `AGENTS.md` | — | Diretrizes de conduta para agentes |
| `.venv/` | — | **Obsoleto.** Antigo venv Python 3.14; use o conda `wdo-backtest` |

Não é repositório git (há `.gitignore`). Sem CI. Estrutura reorganizada em 2026-09-18 (src layout); comportamento verificado idêntico (trades, eventos e equity iguais à linha de base).

## Formato do dado `data/raw/wdo_data.csv`

Exportação padrão do MT5 (History Center):

- Separador **TAB**, campos entre aspas, cabeçalho: `<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>`.
- Ex.: `2026.01.02  09:00:00  5823.950  5825.008  5813.490  5821.990  14620  59883  1`.
- **Cada linha inteira vem entre aspas** (`"a<TAB>b<TAB>c"`), então `pd.read_csv` puro lê uma coluna só. O adaptador **`load_mt5_export`** (em `src/wdo/`) remove as aspas, junta DATE+TIME em `datetime`, escolhe `VOL` (padrão) ou `TICKVOL` como `volume` e chama `validate_bars`. [verificado: carrega 18.900 barras sem erro]
- Alguns preços (ex.: `5825.008`, `5813.490`) não estão no múltiplo de 0,5, sugerindo série **ajustada/contínua** (back-adjusted) ou fonte com preço sintético. **[não verificado]** — descobrir como a série foi construída (rollover, ajuste) é pré-requisito para confiar em PDH/PDL e níveis absolutos.
- Fim dos dados observado: última barra `2026.09.01 14:25`.

## Estado atual (o que se sabe e o que não)

Verificado por leitura de arquivos:

- Motor Python implementa Padrões 1–4, modos de canal 0/1/2, política intrabar, custos, MAE/MFE, métricas e gráficos.
- Testes existem cobrindo: `round_tick`, rejeição de duplicata/OHLC inválido, rollover sobreposto, modos de canal + 1 operação/dia, referência do Padrão 2 com stop/alvo conservador, entrada imediata por RSI (Padrão 4).

**Não verificado:**

- Paridade com o Strategy Tester do MT5.
- Ausência de look-ahead nas EMAs H1/D1 (R1) e demais riscos R2–R7 de 08.
- Natureza da série `data/raw/wdo_data.csv` (ajustada? rollover?).

## Como rodar

Use **sempre** o ambiente conda `wdo-backtest` (ver README desta pasta):

```powershell
conda activate wdo-backtest
pytest -q
jupyter notebook notebooks/01_wdo_opening_backtest.ipynb   # kernel "Python (wdo-backtest)"
```

**Verificado em 2026-09-19** (Python 3.12.14, pandas 3.0.5, motor 1.1.0): `pytest -q` → 77 passed; o notebook executa de ponta a ponta sem erros, lendo `data/raw/wdo_data.csv` via `load_mt5_export` (adaptador adicionado nesta data). O `.venv` (Python 3.14) está obsoleto.

**Aviso metodológico:** este resultado foi obtido na amostra inteira, antes de existir partição de dados, e conta como contaminação registrada (ver 08). É diagnóstico de pipeline, **não** referência de pesquisa; o Baseline V0 oficial será restabelecido no conjunto de pesquisa com o motor congelado.

Primeiro resultado (config padrão, **sem custos e sem slippage**, 2026-01-01 → 2026-09-01, série de origem não auditada — ver R6 em 08): 138 trades (78 long / 60 short), win rate 58,7%, profit factor 0,85, net profit −R$ 840 (−8,4%), max drawdown −17,1%. O win rate de equilíbrio com alvo 6 / stop 10 é 62,5%, então o resultado é negativo **mesmo antes de custos**. Amostra pequena e premissas de execução otimistas (R2–R4): tratar como **diagnóstico do pipeline, não como conclusão sobre a estratégia**. O primeiro trade só ocorre em 2026-02-02 (aquecimento das EMAs D1).

## Premissas e limitações declaradas

- Apenas OHLC M5: **sem ticks, bid/ask, book, latência**. A ordem dos extremos dentro da barra é desconhecida → política `adverse` (pior caso) por padrão.
- O EA no MT5 usa **EMAs H1/D1 "ao vivo"** (barra em formação); o Python usa valores point-in-time defasados. Divergência **intencional e documentada**, mas que muda sinais (ver 02 e 08).
- Custos/slippage/valor do ponto são premissas que o usuário deve ajustar antes de tirar conclusões financeiras.

## Pessoas e ferramentas

- Usuário: Emmanuel (comunicação em **pt-BR**).
- Agentes: Claude Code (VS Code) e, previsivelmente, Codex. Ver [07_agent_protocol.md](07_agent_protocol.md).
- Ambiente: Windows 11, PowerShell/Git Bash, Python 3.14.
- Pasta pai chama-se `Databricks_dev`, mas **este projeto não usa Databricks hoje**.
