# 02 — Especificação da estratégia (EA v1.35) e mapeamento para o Python

Fonte: cabeçalho e `IniciarSessao()` de `reference/mt5/Robo_Abertura_WDO_Genial_v1.35.mq5`; implementação Python em `src/wdo/` (`WDOReplayEngine`). Se este documento e o `reference/mt5/Robo_Abertura_WDO_Genial_v1.35.mq5` divergirem, **o `reference/mt5/Robo_Abertura_WDO_Genial_v1.35.mq5` vence**; corrija este documento.

## Ideia central

Estratégia de **abertura**: só opera a janela inicial do pregão (09:00–10:30), no máximo **1 operação por dia**, com **alvo 6 pts** e **stop 10 pts** fixos. A entrada depende de **onde o dia abre** em relação aos canais do dia anterior, às médias móveis e ao IFR (RSI).

## Insumos

| Item | Definição |
|---|---|
| PDH / PDL | Máxima / mínima do dia anterior |
| Canal superior (`sup`) | `PDH − offset` (offset = 7 pts) |
| Canal inferior (`inf`) | `PDL + offset` |
| EMAs | 13, 17, 21 em **H1** e **D1** (6 valores) |
| IFR | RSI(7), Wilder |
| Abertura | Open da barra M5 das 09:00 |
| `ema_support` / `ema_resistance` | EMA mais próxima **abaixo/igual** e **acima/igual** da abertura |

## Árvore de decisão na abertura

```
abertura > PDH                → Padrão 4 (VENDA, IFR sobrecomprado)
abertura < PDL                → Padrão 4 (COMPRA, IFR sobrevendido)
abertura >= sup (e <= PDH)    → Padrão 3 (VENDA via ordens no canal superior)
abertura <= inf (e >= PDL)    → Padrão 3 (COMPRA via ordens no canal inferior)
senão (entre os canais)       → Padrão 1 (toque de médias), com fallback para Padrão 2
```

## Padrões

### Padrão 1 — toque da média (entre canais)
- Direção: abriu **acima de todas** as EMAs → +1 (compra no toque); **abaixo de todas** → −1 (venda); **entre** as EMAs → direção definida no toque (usa-as como suporte/resistência).
- Gatilho no EA: toque da **primeira média** pelo **preço executável** (tolerância `InpToleranciaEMA` = 1 pt, "compatibilidade Profit").
- Se não tocou na 1ª vela, passa ao Padrão 2.

### Padrão 2 — rompimento da vela anterior (contínuo)
- Abriu entre canais e não tocou médias. **Cada nova vela usa a anterior como referência** até haver entrada: rompeu a **máxima** da anterior → **VENDA**; rompeu a **mínima** → **COMPRA**. (Ou seja, é contra o rompimento — comportamento de fade.)
- v1.31 introduziu a referência contínua (avança vela a vela).

### Padrão 3 — ordens no canal
- Abertura dentro do canal superior → venda; dentro do canal inferior → compra. No Python (`place_channel_orders`), para venda: perna **stop** em `sup − rompe` e perna **limit** (fade) em `PDH + rompe`; para compra: stop em `inf + rompe` e limit em `PDL − rompe`. O cabeçalho do EA descreve "0,5 pt acima/abaixo" de forma ambígua — **conferir os sinais em `ColocarOrdensCanal` (`.mq5`, ~l.509)** antes de confiar.
- `InpModoCanal`: **0** = stop + fade (duas pernas), **1** = só stop (rompe linha de 7 pts), **2** = só fade (rompe PDH/PDL).
- Se as duas pernas forem atingidas na mesma barra, o Python assume o **pior preço para o lado**.
- Ao entrar, ordens pendentes restantes são canceladas.

### Padrão 4 — IFR (fora dos canais)
- **Abaixo da PDL (compra):** IFR 10–16 → compra imediata; IFR < 10 → aguarda vela; IFR > 16 → monitora chegada em 16 (compra imediata ao tocar).
- **Acima da PDH (venda):** espelhado com 86–90 (IFR > 90 → aguarda vela; IFR < 86 → monitora chegada em 86).
- "Aguarda vela": entra na 2ª vela ao tocar a máxima/mínima da 1ª.

## Gestão e regras gerais

- Lote 1 (configurável), stop 10 pts, alvo 6 pts (relação payoff **estruturalmente <1**: precisa de win rate alto — ver 06).
- 1 operação por dia (`gOperouHoje`).
- Fim da janela (10:30): cancela pendentes. **SL/TP anexados permanecem ativos fora da janela** (o Python replica: `process_position` roda em toda barra).
- Posição herdada de dia anterior mantém SL/TP e **bloqueia** nova operação no dia (`POSITION_CARRIED`).
- "Recuperação": se o EA for ligado após a 1ª vela, usa a vela anterior como referência e converte Padrão 1 em 2.

## Mapeamento MQL5 → Python

| Conceito | EA (`reference/mt5/*.mq5`) | Python (`src/wdo/`) |
|---|---|---|
| Parâmetros `input` | bloco `input group` (linhas ~44–68) | `Config` |
| Arredondar preço | `NormPreco` | `round_tick` |
| Iniciar sessão / decidir padrão | `IniciarSessao` | `WDOReplayEngine.start_day` |
| Ordens de canal | `ColocarOrdensCanal` | `place_channel_orders`, `process_pending` |
| Padrões 1/2/4 por vela | `ProcessarPrimeiraVela` / `ProcessarVelaSeguinte` | `signal` |
| Entrada a mercado | `EnviarMercado` | `enter` (aplica slippage e tick) |
| Loop de eventos | `OnTick` | `run` (barra a barra) |
| SL/TP | ordem com stop/alvo | `process_position` + `exit` |
| EMAs / IFR | handles `iMA`/`iRSI` (barra em formação) | `add_point_in_time_indicators`, `rsi_wilder` |

## Divergências conhecidas EA × Python (ver também 08)

1. **EMAs H1/D1 ao vivo vs. point-in-time.** O EA lê o valor "em formação" (shift 0) a cada tick da 1ª vela; o Python usa valores fechados/defasados. Efeito: o Padrão 1 pode disparar de forma diferente.
2. **Toque de média por preço executável (tick) vs. `low/high` da barra M5.** O Python usa `bar.low <= suporte + tolerância` na barra inteira (aproximação otimista de toque).
3. **Padrão 1 só é avaliado na barra de índice 0** no Python; no EA o toque é monitorado tick a tick durante a 1ª vela.
4. **Barra ambígua no Padrão 2** (`low <= ref.low` e `high >= ref.high` na mesma barra): Python entra **COMPRA** ("P2_AMBIGUOUS_LOW_FIRST") — decisão de convenção, não conservadora por construção. Revisar.
5. **Execução:** entrada a mercado usa `bar.open` (barra seguinte/atual), sem spread/bid-ask.
6. **Padrão 4 "aguarda vela":** simplificado no Python; conferir contra `ProcessarVelaSeguinte`.

## Perguntas de especificação em aberto

- O critério exato de "primeira média tocada" quando há EMAs H1 e D1 próximas entre si.
- Se PDH/PDL usam a sessão regular (09:00–18:00) ou incluem pré/after-market e o leilão.
- Como o rollover afeta PDH/PDL no dia da virada do contrato.
