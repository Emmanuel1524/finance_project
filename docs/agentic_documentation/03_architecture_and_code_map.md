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

Módulos: `config.py` (Config, round_tick), `data.py` (loaders/validação/rollover), `indicators.py` (RSI, EMAs), `engine.py` (estado e replay, run_backtest), `metrics.py`, `reporting.py`. Tudo reexportado em `wdo/__init__.py` (`from wdo import Config, run_backtest, ...`).

| Símbolo | Papel |
|---|---|
| `Config` | Dataclass com todos os parâmetros (espelha `input` do EA + custos, tz, capital, `intrabar_policy`). `Config.from_toml('configs/wdo_default.toml')` carrega cenários; chave desconhecida falha. Mutável hoje; recomendável `frozen=True`. |
| `round_tick` | Arredonda ao tick (0,5). |
| `validate_bars` | Valida e normaliza OHLCV. Levanta `ValueError` em vez de corrigir silenciosamente. |
| `load_mt5_export` | Lê a exportação bruta do MT5 (linhas entre aspas, TAB, `<DATE>/<TIME>`), normaliza e valida. |
| `load_csv_or_parquet`, `load_http_ohlcv` | Loaders (esperam colunas já normalizadas). |
| `build_continuous_contract` | Concatena contratos por calendário de rollover explícito; falha em sobreposição/cobertura. |
| `rsi_wilder` | RSI com EWM `alpha=1/period`. |
| `add_point_in_time_indicators` | EMAs H1/D1 e RSI defasados (`shift(1)`). **Ver risco em 08.** |
| `PendingOrder`, `Position`, `BacktestResults` | Estruturas de estado/saída. |
| `WDOReplayEngine` | Simulador. Métodos: `start_day`, `place_channel_orders`, `process_pending`, `signal`, `process_position`, `enter`, `exit`, `fill`, `event`, `run`. |
| `run_backtest` | Fachada: filtra datas e roda o motor. |
| `metrics` | Dicionário de métricas (estilo relatório MT5). |
| `print_backtest_report`, `plot_results` | Saída/visualização (módulo `reporting.py`). |

## Contratos e invariantes do motor

- Entrada: DataFrame com `datetime, open, high, low, close, volume` (tz-aware ou naive interpretado como Brasília; ambiguidade de DST levanta erro).
- Saída `trades`: `trade_id, side, entry_*, exit_*, quantity, stop_price_inicial, target_price_inicial, exit_reason, gross_pnl, costs, net_pnl, duration, equity_after_trade, MAE, MFE`.
- Saída `equity`: `datetime, equity, cash, in_position` por barra (equity marcada a mercado no close).
- Saída `events`: `datetime, event, detail` (`SESSION`, `ENTRY`, `EXIT`…) — trilha de auditoria.
- Invariantes esperados: ≤1 posição por vez; ≤1 trade/dia; stop/alvo do lado correto; `net_pnl = (saída−entrada)·lado·qtd·valor_ponto − 2·qtd·(comissão+taxas)`; posição aberta no fim dos dados é fechada como `END_OF_DATA`.
- `exit_reason` relevantes: `STOP_LOSS`, `TAKE_PROFIT`, `STOP_INTRABAR_AMBIGUOUS`, `TARGET_INTRABAR_AMBIGUOUS`, `END_OF_DATA`.
- Tags de entrada: `P1_EMA`, `P1_EMA_DOUBLE`, `P2_LOW`, `P2_HIGH`, `P2_AMBIGUOUS_LOW_FIRST`, `P3_STOP`, `P3_LIMIT`, `P4_RSI`, `P4_WAIT_REFERENCE`.

## Pontos de atenção de design (dívida técnica)

- Estilo denso (várias instruções por linha) dificulta revisão e diff; prefira legibilidade ao editar.
- ~~Motor, I/O, métricas e plot no mesmo arquivo~~ separados em módulos (2026-09-18). Falta separar `strategy/` (regras puras) de `engine/` (execução/custos).
- Estado do dia (`day_state`) é dicionário sem esquema; migrar para dataclass tipada.
- Slippage é aplicado simetricamente em entrada e saída via `fill`, inclusive em saídas de alvo/stop (para alvo limit, modelar slippage zero é mais fiel; decisão a documentar).
- Sem logging; sem tipagem estrita; sem cobertura de teste para P1 `EMA_DOUBLE`, P3 ambos os modos completos com slippage, posição herdada, e `end of data`.

## Testes existentes (`tests/test_wdo_backtest.py`)

1. `test_round_tick`
2. `test_reject_duplicate_and_bad_ohlc`
3. `test_rollover_rejects_overlap`
4. `test_channel_modes_and_one_operation_per_day`
5. `test_p2_reference_and_conservative_stop_target`
6. `test_p4_immediate_rsi_entry`

Cobertura de look-ahead, paridade com MT5, golden files e propriedades: **inexistente**.

## Estrutura do repositório

Ver `../../README.md` e `../../CLAUDE.md` §7.
