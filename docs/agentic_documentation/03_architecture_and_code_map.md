# 03 — Arquitetura e mapa do código

## Fluxo de dados

```
MT5 export (data/raw/wdo_data.csv, TAB, DATE/TIME separados)
      │  load_mt5_export(): remove aspas, DATE+TIME → datetime, escolhe volume
      ▼
validate_bars()  ── tz America/Sao_Paulo, sem duplicatas, OHLC válido, sem lacunas 5–60 min
      │
      ├── (opcional) build_continuous_contract(raw, rollover, start, end, tz)
      ▼
run_backtest(bars, start, end, initial_capital, config)
      │  filtra período → WDOReplayEngine(config).run()
      ▼
add_point_in_time_indicators()  → EMA 13/17/21 H1 e D1, RSI(7) (defasados)
      │
      ▼  loop por dia → por barra
start_day → process_position → process_pending → signal → equity
      ▼
BacktestResults(trades, equity, events, config)
      ▼
metrics() / print_backtest_report() / plot_results()
```

## `src/wdo/` — módulos e símbolos públicos

Módulos: `config.py` (Config, round_tick), `data.py` (loaders/validação/rollover), `indicators.py` (RSI, EMA de candle fechado), `strategies/` (`base.py`: contrato `Strategy`; `baseline_v0.py`: regras do V0), `engine.py` (simulador: execução, gaps, custos, `ENGINE_VERSION`), `partitions.py` (partições e guarda de acesso), `metrics.py`, `reporting.py`. Tudo reexportado em `wdo/__init__.py` (`from wdo import Config, run_backtest, ...`).

| Símbolo | Papel |
|---|---|
| `Config` | Dataclass com todos os parâmetros (espelha `input` do EA + custos, tz, capital, `intrabar_policy`). `Config.from_toml('configs/wdo_default.toml')` carrega cenários; chave desconhecida falha. Mutável hoje; recomendável `frozen=True`. |
| `round_tick` | Arredonda ao tick (0,5). |
| `validate_bars` | Valida e normaliza OHLCV. Levanta `ValueError` em vez de corrigir silenciosamente. |
| `load_mt5_export` | Lê a exportação bruta do MT5 (linhas entre aspas, TAB, `<DATE>/<TIME>`), normaliza e valida. |
| `load_csv_or_parquet`, `load_http_ohlcv` | Loaders (esperam colunas já normalizadas). |
| `build_continuous_contract` | Concatena contratos por calendário de rollover explícito; falha em sobreposição/cobertura. |
| `rsi_wilder` | RSI com EWM `alpha=1/period`. |
| `closed_candle_ema`, `add_point_in_time_indicators` | EMA H1/D1 do **último candle fechado** (sobre candles existentes) e RSI até a barra anterior. Verificados por testes de mutação/truncamento. |
| `Strategy`, `OrderIntent`, `SessionOpen`, `SessionDecision`, `BarOpen` | Contrato estratégia ↔ simulador: a estratégia vê só a abertura da barra e barras fechadas e devolve ordens (`market`/`stop`/`limit`). |
| `ExitSpec` | Instrução de saída por trade anexada a uma `OrderIntent` (motor 1.1.0): stop por pontos ou nível (obrigatório), alvo opcional, trailing, saída por horário. Sem ela vale o `Config` (V0). |
| `BaselineV0` | Regras do EA v1.35 (Padrões 1–4). |
| `Position`, `BacktestResults` | Estruturas de estado/saída (`BacktestResults` inclui `engine_version` e `strategy_name`). |
| `WDOReplayEngine` | Simulador. Métodos: `level_fill`, `select_entry`, `open_position`, `manage_entry_bar`, `process_position`, `update_trailing`, `resolve_exit`, `exit`, `process_session_bar`, `run`. `ENGINE_VERSION = 1.1.0`. |
| `run_backtest` | Fachada: aquece indicadores com histórico anterior, descarta barras após o fim da janela e roda o motor. |
| `Partitions`, `select`, `load_partition_bars`, `run_partition_backtest` | Partições de dados (D1) e guarda: validação/holdout só com `authorized=True`. |
| `metrics` | Dicionário de métricas (estilo relatório MT5). |
| `print_backtest_report`, `plot_results` | Saída/visualização (módulo `reporting.py`). |

## Contratos e invariantes do motor

- Entrada: DataFrame com `datetime, open, high, low, close, volume` (tz-aware ou naive interpretado como Brasília; ambiguidade de DST levanta erro).
- Saída `trades`: `trade_id, side, entry_* (inclui `entry_reason`), exit_*, quantity, stop_price_inicial, target_price_inicial, exit_reason, gross_pnl, costs, net_pnl, duration, equity_after_trade, MAE, MFE`.
- Saída `equity`: `datetime, equity, cash, in_position` por barra (equity marcada a mercado no close).
- Saída `events`: `datetime, event, detail` (`SESSION`, `ENTRY`, `EXIT`…) — trilha de auditoria.
- Invariantes esperados: ≤1 posição por vez; ≤1 trade/dia; stop/alvo do lado correto; `net_pnl = (saída−entrada)·lado·qtd·valor_ponto − 2·qtd·(comissão+taxas)`; posição aberta no fim dos dados é fechada como `END_OF_DATA`.
- `exit_reason` relevantes: `STOP_LOSS`, `STOP_LOSS_ENTRY_BAR`, `TAKE_PROFIT`, `STOP_INTRABAR_AMBIGUOUS`, `TARGET_INTRABAR_AMBIGUOUS`, `END_OF_DATA`.
- Tags de entrada: `P1_EMA`, `P1_EMA_DOUBLE`, `P2_LOW`, `P2_HIGH`, `P2_AMBIGUOUS_LOW_FIRST`, `P3_STOP`, `P3_LIMIT`, `P4_RSI`, `P4_WAIT_REFERENCE`.

## Pontos de atenção de design (dívida técnica)

- Estilo denso (várias instruções por linha) dificulta revisão e diff; prefira legibilidade ao editar.
- ~~Motor, I/O, métricas e plot no mesmo arquivo~~ separados em módulos (2026-09-18). Falta separar `strategy/` (regras puras) de `engine/` (execução/custos).
- `BaselineV0` guarda o estado do dia em atributos simples; ok para o V0, revisar se candidatos ficarem complexos.
- Slippage é aplicado simetricamente em entrada e saída via `fill`, inclusive em saídas de alvo/stop (para alvo limit, modelar slippage zero é mais fiel; decisão a documentar).
- Sem logging; sem tipagem estrita; sem cobertura de teste para P1 `EMA_DOUBLE`, P3 ambos os modos completos com slippage, posição herdada, e `end of data`.

## Testes existentes (77; `pytest -q`)

`test_wdo_backtest.py` (6 originais, adaptados), `test_execution.py` (nível, gap, barra de entrada, custos), `test_indicators.py`, `test_leakage.py` (com controles negativos), `test_partitions.py`, `test_exit_capability.py` (ExitSpec: validação, alvo opcional, horário, trailing, gaps, barra de entrada e vazamento) e `test_engine_frozen.py` (regressão do motor; idêntica na 1.0.0 e na 1.1.0). Os 6 testes originais:

1. `test_round_tick`
2. `test_reject_duplicate_and_bad_ohlc`
3. `test_rollover_rejects_overlap`
4. `test_channel_modes_and_one_operation_per_day`
5. `test_p2_reference_and_conservative_stop_target`
6. `test_p4_immediate_rsi_entry`

Cobertura de vazamento e golden de regressão: existe (ver acima). Paridade com o MT5 (Strategy Tester) e testes por propriedade (hypothesis): **inexistentes**.

## Estrutura do repositório

Ver `../../README.md` e `../../CLAUDE.md` §7.
