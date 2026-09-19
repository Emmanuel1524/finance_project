# 05 — Guia de replay trading (simulação bar-by-bar)

"Replay" aqui significa **reexecutar a lógica do robô sobre dados históricos, evento a evento, na mesma ordem em que o robô viveria**, em vez de calcular sinais vetorizados sobre a série inteira. É a abordagem adequada para estratégias com **estado** (ordens pendentes, posição, 1 trade/dia, referência que avança vela a vela), como esta.

## 1. Princípios

1. **Causalidade estrita:** em cada passo o motor só conhece o passado + a barra corrente *na medida em que ela já poderia ser conhecida* (ver §3).
2. **Mesma máquina de estados do robô:** estados do EA (`gEstado`, `gPadrao`, `gDirecao`, `gOperouHoje`) ↔ `day_state` no Python. Cada transição deve ter equivalente rastreável.
3. **Ordem de eventos por barra** explícita e testada.
4. **Conservadorismo onde há incerteza:** com OHLC não se sabe se o high veio antes do low. Sempre resolver a ambiguidade contra a estratégia (`adverse`).
5. **Auditabilidade:** cada decisão gera um evento com motivo.

## 2. Ordem de processamento por barra (motor 1.0.0)

Para cada dia → para cada barra M5 `b`:

1. `process_position(b)`: posição aberta em barra **anterior**. Atualiza MAE/MFE; stop/alvo com gap (stop no pior entre o stop e a abertura; alvo no melhor). Stop e alvo na mesma barra → política intrabar (padrão: **stop**).
2. Se `b` está na janela de operação: a estratégia recebe **só a abertura de `b`** e a barra anterior fechada (`on_bar_open`) e devolve ordens. O simulador decide a execução (`select_entry`): a mercado na abertura; ordens a nível tocadas no nível (ou na abertura, se houve gap além do nível); mesmo lado na mesma barra ⇒ **pior preço**; lados opostos ⇒ prioridade declarada pela estratégia.
3. Se entrou: `manage_entry_bar(b)` — stop avaliado pela barra inteira (hipótese adversa), alvo só a partir da barra seguinte.
4. `on_bar_close(b)` atualiza o estado da estratégia; equity marcada no `close`.
5. Fim do dia: limpa pendentes.

SL/TP seguem ativos fora da janela (como ordens anexadas no MT5).

## 3. O problema central do OHLC

Uma barra M5 revela `open, high, low, close`, mas **não a sequência**. Consequências e tratamento:

| Situação | Problema | Tratamento conservador |
|---|---|---|
| Stop e alvo dentro do range da mesma barra | Não se sabe qual veio primeiro | Assumir **stop** (`adverse`) |
| Duas ordens pendentes atingidas na mesma barra | Qual executou? | Escolher o **pior preço** para o lado |
| Padrão 2: barra rompe máxima e mínima da referência | Compra ou venda? | Convenção atual = compra (`P2_AMBIGUOUS_LOW_FIRST`) — **não é conservadora por construção; revisar** |
| Entrada por toque de nível dentro da barra | Só o toque, não o preço executável | **Implementado (D5):** entra no **nível de toque** (ou na abertura se já houve gap além do nível), slippage contra, dentro do range da barra; nunca no `open` de uma barra cujo `high/low` disparou o sinal |
| Entrada a mercado após sinal na barra t | Não dá para operar o close de t | Entrar na **abertura de t+1** (não no close de t) |

Regra de ouro: **um sinal calculado com o close da barra t só pode ser executado a partir da barra t+1**.

## 4. Modelo de execução

- **Preços:** arredondados ao tick (0,5). Nunca preencher em preço fora do range OHLC da barra.
- **Slippage:** configurável em pontos; aplicar contra o trader (compra mais caro, venda mais barata). Saídas por *limit* (alvo) normalmente têm slippage ~0; saídas por *stop* têm slippage ≥ 0. Documentar a escolha.
- **Custos:** corretagem + emolumentos por contrato, ida e volta (`2·qtd·(comissão+taxas)` no motor).
- **Spread:** ausente nos dados OHLC (coluna `SPREAD` do MT5 é informativa). Modelar via slippage ou usar dados com bid/ask.
- **Fila / preenchimento parcial:** ignorados (1 contrato, alta liquidez do WDO na abertura; premissa a validar).
- **Gaps e leilão (implementado):** stop (pendente ou de saída) executa no **pior** entre o nível e a abertura da barra; alvo/limit no melhor (fill real na abertura). Slippage é simétrico em entrada e saída, inclusive no alvo (conservador).

## 5. Integridade temporal e point-in-time

**Regra:** no instante `t`, uma decisão de trading só pode usar informação que estaria disponível **em ou antes de `t`**. `t` é o instante em que a estratégia agiria (abertura da barra, toque de um nível, fechamento). **Timing ambíguo ⇒ premissa mais conservadora:** o dado é tratado como conhecido *mais tarde* e a execução ocorre *mais tarde* e/ou *pior*.

**Verificações explícitas.** Toda mudança de indicador, feature, filtro, sinal ou regra passa por esta revisão de código; qualquer ocorrência é FAIL até ser justificada e provada segura:

| Vazamento | O que procurar |
|---|---|
| **Candle futuro** | Uso da barra t+k (k>0); uso de `high/low/close` da barra corrente numa decisão tomada na **abertura** dessa barra |
| **Referência futura explícita** | `shift(-n)`, `diff(-n)`, `pct_change(-n)`, `.iloc[i+k]`, `bfill`, `reindex(method="bfill"/"nearest")`, `merge_asof(direction="forward"/"nearest")`, laços que olham índices à frente |
| **Janelas centradas / bidirecionais** | `rolling(..., center=True)`, `filtfilt`, `interpolate`, suavizações e decomposições que usam os dois lados |
| **Indicador com observações futuras** | Indicador calculado sobre a série inteira e depois "cortado"; `resample().last()/max()/min()` que inclui barras posteriores a `t` |
| **H1/D1 incompleto** | Valor do candle H1/D1 **em formação** ou que já inclui barras após `t`; `shift` aplicado em linhas M5 em vez de no índice do timeframe maior. Correto: usar o **último candle fechado**, deslocando no índice do timeframe maior **antes** de reindexar para M5 |
| **Agregado do dia corrente tratado como final** | `high/low/close/volume/range` do dia atual antes do fim da sessão. PDH/PDL vêm só do dia **anterior** já encerrado; máxima/mínima "do dia" não entram em decisões intradiárias |
| **Pré-processamento ajustado com dados futuros** | Normalização, z-score, scalers, percentis, limiares derivados de estatísticas da amostra inteira, PCA/clustering/regimes ajustados na série completa. Usar apenas estatísticas causais (expanding/rolling) ou ajustadas no conjunto de pesquisa e congeladas |
| **Timing de execução** | Sinal derivado de `close` (ou de `high/low`) da barra t executado antes de essa informação existir. Gatilho intrabar (toque de nível) **nunca** gera entrada no `open` da mesma barra: entrada no nível de toque + slippage (ou na abertura de t+1). Regra de ouro: **sinal com o close de t só executa a partir de t+1** |
| **Vazamento via feature engineering** | Rótulo/resultado/PnL do trade usado como feature; agrupar/ordenar por informação de fim de dia; `merge` por data sem alinhar o horário; calendário/feriados "futuros"; escolher features, regras ou parâmetros olhando validação/holdout |
| **Partições** | Dados de validação/holdout influenciando o desenho de qualquer candidato. Aquecimento (*warm-up*) de indicadores usa só barras **anteriores** à janela avaliada, nunca posteriores |

**Pergunta obrigatória para toda feature, indicador, filtro ou sinal novo:**

> *"Este valor exato poderia ter sido conhecido neste exato timestamp em operação real?"*

Resposta incerta ⇒ a feature é **insegura** e não é usada até ser verificada. A resposta e a evidência entram no relatório do experimento ([07 §5](07_agent_protocol.md)).

**Regras de construção:**
- Decisão na abertura de t usa apenas barras **fechadas** (≤ t−1). Decisão no fechamento de t usa ≤ t e executa de t+1 em diante.
- **EMA "ao vivo" do MT5 (barra em formação):** só é reproduzível com ticks/M1. Com M5, usar candles fechados (conservador; diverge do EA) e documentar o impacto; nunca uma aproximação que use a barra inteira.
- Indicadores vetorizados sobre a série completa só são aceitos se **comprovadamente causais** pelos testes da §11.
- **Aquecimento (implementado):** `run_backtest` recebe histórico anterior à janela para aquecer os indicadores e **descarta barras posteriores ao fim da janela**; só se opera dentro de [início, fim]. Assim reavaliar uma partição não muda decisões passadas e o futuro nunca entra.

## 6. Rollover e série contínua

- WDO tem vencimento mensal. Definir e documentar: data/critério de rollover (calendário fixo vs. volume), e se a série é **ajustada** (back-adjusted) ou **não ajustada**.
- Em série ajustada, níveis absolutos (PDH/PDL) ficam deslocados e **não coincidem com o que o robô viu na plataforma**; em não ajustada, o dia de rollover cria um salto artificial. Nenhum dos dois é "correto" universalmente: **depende do uso** (estratégia baseada em níveis do dia anterior prefere série não ajustada com PDH/PDL calculados dentro do mesmo contrato).
- Nunca deixar o dia da virada gerar sinal por causa do salto.

## 7. Calendário de pregão

- Feriados B3, pregão encerrado mais cedo, dias sem abertura → o motor não deve inventar dias nem preencher lacunas silenciosamente (`validate_bars` falha em lacunas de 5 a 60 min).
- Horários: sempre `America/Sao_Paulo` tz-aware.

## 8. Do replay ao paper trading e produção

O mesmo núcleo de decisão deve ser reutilizável ao vivo:

- Separar **decisão** (função pura: estado + barra → ordens desejadas) de **execução** (backtest: simulador de fills; live: adaptador de corretora).
- **Idempotência** de envio de ordem; reconciliação de posição/ordens ao iniciar.
- **Shadow mode:** rodar a estratégia ao vivo sem enviar ordens, comparando sinais com o backtest sobre o mesmo dia.
- **Comparar fills reais × simulados** para calibrar slippage.

## 9. Checklist de replay

- [ ] Revisão de look-ahead concluída com a tabela da §5 (sem FAIL)
- [ ] Pergunta "este valor poderia ser conhecido neste timestamp?" respondida para cada feature nova
- [ ] Testes de vazamento da §11 executados (ou N/A justificado)
- [ ] Sinal só executa em barra posterior à do dado usado; gatilho intrabar não executa no `open` da mesma barra
- [ ] Ambiguidade intrabar resolvida contra a estratégia e documentada
- [ ] Barra de entrada tratada de forma conservadora (stop/alvo avaliados após a entrada)
- [ ] Fills dentro do range OHLC e no tick
- [ ] Custos, comissão e slippage aplicados
- [ ] Indicadores multi-timeframe usam apenas candles fechados
- [ ] Rollover/PDH/PDL tratados por contrato
- [ ] Partições respeitadas (sem dados de validação/holdout; aquecimento só com passado)
- [ ] Eventos logados com motivo; execução determinística

## 10. Integridade da simulação durante a pesquisa

A pesquisa de estratégias ([06](06_quant_finance_playbook.md), [07](07_agent_protocol.md)) compara candidatos **sobre o mesmo simulador**. Por isso a simulação é um instrumento de medida que não pode ser ajustado para favorecer um candidato.

**Invariantes que todo experimento preserva (candidato ou baseline):** processamento estritamente cronológico; sem look-ahead; indicadores point-in-time; interpretação conservadora do OHLC, sem premissa favorável quando a ordem intrabar é ambígua; regras de sessão vigentes; ciclo de vida de ordens; limite diário de trades; custos, comissão e slippage; tratamento de rollover; premissas de timezone. Premissas de execução são **idênticas para todos os candidatos**; sensibilidade a elas é aplicada a todos do mesmo modo.

**Congelamento do motor:**
- O motor tem uma versão identificada; todo resultado registra a versão. **Nunca comparar resultados obtidos em versões diferentes do motor**: se o motor mudar, o Baseline V0 e os candidatos relevantes são reexecutados na nova versão.
- Mudança de motor só é aceitável como **correção de erro de simulação** (ex.: R1–R5 em [08](08_roadmap_and_open_questions.md)), justificada por erro de modelagem e não por efeito no desempenho, com teste que reproduz o erro, aprovação do usuário e **nunca no mesmo experimento** que uma mudança de estratégia. O efeito no V0 é reportado como consequência, não como objetivo.
- **Estado (2026-09-19):** as correções do G0 (R1, R4, R8, R9, R10; ver 08) foram feitas e o motor está na versão **`ENGINE_VERSION = 1.0.0`**, protegido por `tests/test_engine_frozen.py`. Mudar comportamento exige: aprovação do usuário, nova versão, atualizar a referência desse teste e reexecutar V0 e candidatos relevantes.

**Problema no motor descoberto durante a pesquisa (procedimento obrigatório):**
1. **Parar** a pesquisa; não continuar comparando candidatos.
2. **Documentar a suspeita:** arquivo/trecho, comportamento esperado × observado e evidência mínima reproduzível (barras sintéticas, se possível).
3. **Explicar por que afeta a correção da simulação** (e não apenas o desempenho): qual regra de replay ([§1](#1-princípios), [§5](#5-integridade-temporal-e-point-in-time)) é violada.
4. **Pedir aprovação** ao usuário antes de mudar qualquer coisa.
5. A correção é uma **tarefa separada** de qualquer experimento de estratégia, com teste que reproduz o erro. Depois dela, V0 e candidatos relevantes são reexecutados na nova versão; resultados anteriores ficam marcados como **obsoletos** (nunca apagados).

**Separação estratégia × simulação (feita em 2026-09-19):** o simulador (`engine.py`) executa qualquer `Strategy` (contrato em `strategies/base.py`); as regras do V0 vivem em `strategies/baseline_v0.py`. A estratégia só vê a abertura da barra corrente e barras já fechadas; gatilhos que dependem do range da barra chegam como ordens a nível (`stop`/`limit`), e o simulador decide se e a que preço executam. Candidatos são novos arquivos em `strategies/`; editar `engine.py` continua exigindo o procedimento acima.

**Limitações do M5:** onde o OHLC M5 não reproduz o comportamento tick a tick do MT5 (toque intrabar de nível, EMAs em formação, bid/ask, fila, gaps de leilão), a limitação é **documentada** (§3–4 e R2–R5 em 08) e tratada com a premissa conservadora — nunca com uma premissa otimista que "aproxime" o EA e melhore o resultado.

## 11. Testes automatizados de vazamento

Objetivo: provar que decisões passadas **não dependem de dados futuros**. Implementar sempre que tecnicamente praticável; são obrigatórios para todo indicador/sinal novo e devem passar para o Baseline V0 antes do congelamento do motor (G0 em [08](08_roadmap_and_open_questions.md)). São testes de integridade — escrevê-los não é alterar a estratégia. Rodar em dados sintéticos e no conjunto de pesquisa; **nunca** no holdout. Usar vários `T` (primeira barra do dia, meio da sessão, virada de hora/dia/contrato).

| Teste | Procedimento | Critério |
|---|---|---|
| **Mutação do futuro** | Rodar até o timestamp `T`; alterar **todas** as observações posteriores a `T` (ruído, valores extremos, inversão; manter OHLC válido) e rodar de novo | Sinais, ordens, fills, eventos e estado diário com timestamp ≤ `T` **idênticos** |
| **Histórico truncado** | Rodar só com dados até `T` e comparar com a execução na série completa | Decisões até `T` **idênticas** |
| **Mutação da mesma barra** | Alterar `high/low/close` (mantendo `open`) da barra `T` | Decisões e preços de entrada tomados **na abertura** de `T` não mudam. Detecta gatilho intrabar executado no `open` |
| **Reprodutibilidade do sinal** | Para o mesmo histórico até `T`, comparar estado e decisão gerados, independentemente do que exista depois (teste de propriedade, parametrizado em `T`) | Estado (`day_state`) e decisão idênticos |

**Se um teste falhar:** investigar o vazamento **antes de continuar**. Em experimento, isso é `Look-ahead review: FAIL` e o resultado **não é aceito** ([07 §5](07_agent_protocol.md)); se a causa estiver no motor, aplicar o procedimento da §10.

**Implementação:** `tests/test_leakage.py` (mutação do futuro, histórico truncado, reprodutibilidade do sinal e mutação da mesma barra, cada um com **controle negativo** que prova que o teste detecta um indicador com vazamento) e `tests/test_indicators.py` (EMA de candle fechado × EMA manual, IFR defasado, mutação e truncamento no nível dos indicadores).
