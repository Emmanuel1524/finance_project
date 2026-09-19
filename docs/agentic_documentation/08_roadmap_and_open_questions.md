# 08 — Riscos conhecidos, dívidas técnicas, roadmap e perguntas abertas

Baseado em **leitura** do código em 2026-09-18. Nada abaixo foi confirmado por execução, salvo onde indicado. Cada item deve virar teste ou ser descartado com evidência. Riscos R1–R5 e R7–R9 são candidatos a **correções de simulação** do portão G0 (ver Roadmap), não a otimização de estratégia.

## Riscos de correção (prioridade alta)

**Resolução no G0 (2026-09-19, motor 1.0.0):** R1 (EMAs de candle fechado; deslocamento no timeframe maior) **e um segundo defeito, R1b** (a EMA era calculada sobre a grade horária/diária com buracos de madrugada e fim de semana, o que fazia o `ewm` decair pesos e divergir da EMA do MT5; confirmado em experimento sintético: 9,47 × 8,375), R4 (gap-through), R8 (entrada a nível, nunca no `open` de uma barra cujo `high/low` disparou o sinal), R9 (barra de entrada com hipótese adversa) e **R10 (novo)**. **R10:** com duas ordens do mesmo lado tocadas na mesma barra, o código antigo escolhia o **melhor** preço (`min` para compra, `max` para venda), contrariando o próprio comentário e o princípio adverso; agora vale o **pior**. Verificação de fidelidade do port: com as EMAs antigas, as 96 entradas da partição de pesquisa coincidem 96/96 em data-hora e lado com a linha de base antiga (só as tags do desempate R10 mudam, 6 casos). **Em aberto:** R2, R3, R5 (mantido conservador), R6, R7. Os detalhes históricos de cada risco seguem abaixo.


### R1 — Look-ahead nas EMAs H1/D1 (`add_point_in_time_indicators`) — **CORRIGIDO no motor 1.0.0 (2026-09-19)**
- O código faz `close.resample("1h").last().ewm(...)`, `reindex(data.index, method="ffill")` e depois `.shift(1)`.
- O `.shift(1)` ocorre **depois** do reindex para M5, então desloca **uma linha M5 (5 min)**, não um candle H1/D1. Para uma barra M5 no meio de uma hora/dia, o valor da EMA do bucket corrente já incorpora o **fechamento final desse bucket** (informação futura).
- **Mitigação atual (fortuita):** as EMAs só são consumidas na **primeira barra da sessão** (`start_day`), onde a linha anterior pertence ao bucket do dia/hora anterior; por isso o impacto prático pode ser pequeno. Ainda assim H1 na barra das 09:00 pode ficar defasado (não usa o candle H1 das 08:xx, que não existe) e qualquer uso futuro das EMAs em outras barras vaza informação.
- **Ação:** deslocar no índice do timeframe maior antes do reindex; escrever os testes de truncamento e de mutação do futuro ([05 §11](05_replay_trading_guide.md)) (alterar dados posteriores a t não muda o valor em t). [não verificado por execução]

### R2 — Toque de EMA com `low/high` da barra inteira
- O Padrão 1 usa `bar.low <= suporte + tolerância` na barra M5 da abertura. No EA é o **preço executável em tempo real**. A barra inteira pode registrar toque que, na prática, ocorreu tarde ou com preço diferente. Efeito provável: sinais mais frequentes/otimistas que o EA real.

### R3 — Ambiguidade do Padrão 2 resolvida como COMPRA
- Quando a barra rompe a máxima e a mínima da referência, o código escolhe compra (`P2_AMBIGUOUS_LOW_FIRST`). Não é necessariamente o pior caso; para ser consistente com "adverse", avaliar o resultado nos dois sentidos e adotar o pior, ou marcar o trade como ambíguo e excluí-lo/estressá-lo.

### R4 — Preenchimento de ordens stop no preço da ordem (sem gap-through) — **CORRIGIDO no motor 1.0.0**
- Ordens pendentes e stops de saída executam exatamente no preço da ordem. Na abertura (leilão, gaps) isso é otimista. Modelar preenchimento no pior entre preço da ordem e `open` da barra quando há gap.

### R5 — Slippage simétrico também no alvo — **mantido (conservador), documentado**
- `fill` aplica `slippage_points` em toda entrada/saída, inclusive em alvo (limit). Decidir e documentar: alvo sem slippage, stop com slippage.

### R6 — Série ajustada (adaptador já existe) — **evidência forte, ainda não auditada**
- O adaptador `load_mt5_export` resolve o formato (ver 01). Continua em aberto: preços não múltiplos de 0,5 sugerem série ajustada (**[não verificado]**). Se ajustada, PDH/PDL e níveis diferem do real.
- Não há tabela de rollover no repositório; `data/raw/wdo_data.csv` não tem coluna `contract`.

**Nota R6 (2026-09-19):** verificado que **100% das linhas** de `data/raw/wdo_data.csv` têm ao menos um preço OHLC fora do tick de 0,5 (ex.: 5825,008). A série é, quase certamente, ajustada/derivada. Consequências: níveis absolutos (PDH/PDL) não coincidem com o que o robô viu na plataforma, e o arredondamento ao tick do motor pode deslocar um fill por até meio tick (os invariantes de "preço dentro do range" toleram meio tick por isso).

### R7 — `validate_bars` rejeita lacunas de 5 a 60 min
- Qualquer lacuna intradiária (ex.: falha do feed, intervalo de leilão) derruba a carga inteira. Pode ser correto (falha alto), mas precisa de política: relatar e decidir, ou tratar dias problemáticos explicitamente.

### R8 — Entrada no `open` da barra com gatilho definido por `high/low` da mesma barra — **CORRIGIDO no motor 1.0.0**
- Em P1 (`P1_EMA`, `P1_EMA_DOUBLE`), P2 (`P2_LOW/HIGH/AMBIGUOUS`) e P4 (`P4_WAIT_REFERENCE`) o gatilho usa `bar.low`/`bar.high` da barra corrente, mas a entrada é preenchida em `bar.open` (`engine.py`, `signal`). O `open` é conhecido antes do `high/low` que dispara o sinal: viola a regra de timing de [05 §5](05_replay_trading_guide.md) (gatilho intrabar não executa no `open` da mesma barra). O preço de entrada pode ser melhor que o real, e o sinal usa informação não disponível na abertura.
- **Ação:** decisão de convenção de entrada (nível de toque + slippage ou abertura da barra seguinte) — D5/D6; teste "mutação da mesma barra" (05 §11) deve reproduzir o problema.

### R9 — Barra de entrada sem avaliação de stop/alvo — **CORRIGIDO no motor 1.0.0**
- No laço `run`, `process_position(bar)` roda **antes** de `process_pending`/`signal`; uma posição aberta na barra t só tem stop/alvo avaliados a partir de t+1. O movimento restante da própria barra de entrada (incluindo stop atingido) é ignorado, o que é otimista e distorce MAE/MFE e durações.
- **Ação:** definir tratamento conservador da barra de entrada (avaliar stop/alvo após a entrada com ordem adversa) — D5.

### Evidências vindas da primeira execução (2026-09-18) — diagnóstico de pipeline, **obsoleto**: motor v0 (antes do G0), amostra inteira, sem custos
- **R4 confirmado nos dados:** o trade 1 tem MAE de R$ 255,95 (≈ 25,6 pts) com stop de 10 pts e saída exatamente no stop: houve gap além do stop, mas o motor preenche no preço do stop. A perda real seria maior que R$ 100.
- Todas as perdas e ganhos saem exatamente −R$ 100 / +R$ 60 (sem slippage nem custos) → o resultado é hipersensível a qualquer custo: com win rate de 58,7% vs. equilíbrio de 62,5%, o resultado já é negativo sem custos.
- **Aviso de código:** `plot_results` emite `UserWarning: Converting to PeriodArray/Index representation will drop timezone information` (`src/wdo/`, gráfico "Trades por mês"). Inofensivo, mas convém tratar.
- pandas 3.0.5 (ambiente conda) executa o motor sem erros; os testes passam.

## Dívidas técnicas

- Estilo denso (várias instruções por linha) em `engine.py`/`metrics.py`/`reporting.py`. (Módulos já separados em 2026-09-18.)
- `Config` mutável; `day_state` como dicionário livre.
- Sem lockfile, ruff/mypy, CI, logging (`pyproject.toml` existe desde 2026-09-18).
- Git iniciado em 2026-09-19; primeiro commit realizado.
- Dependências com versões `>=` em `environment.yml`/`pyproject.toml` (pinar ao produtizar).
- Testes (77): faltam paridade com o MT5, testes por propriedade (hypothesis), posição herdada entre dias e `END_OF_DATA` explícito.
- `metrics()` calcula `Consecutive Wins` de forma que precisa ser revisada (agrupamento por `signs`); verificar contra casos simples. [não verificado]

## Roadmap: portões e fases

Metodologia em [06](06_quant_finance_playbook.md); protocolo do agente em [07](07_agent_protocol.md); integridade da simulação em [05](05_replay_trading_guide.md). **Estado atual: antes do G1 — a Fase 1 não está autorizada.**

**Já feito (2026-09-18):** ambiente conda `wdo-backtest`, notebook end-to-end, adaptador `load_mt5_export`, reorganização em `src/wdo/`.

**G0 implementado (2026-09-19), aguardando commit e G1:** correções R1/R1b/R4/R8/R9/R10; estratégia separada do simulador (`strategies/`); custos provisórios (D6) e partições (D1) em `configs/`; guarda de partições; suíte de testes de vazamento com controles negativos; motor 1.0.0 congelado com teste de regressão; notebook restrito à partição de pesquisa. `pytest`: 45 passed.

### G0 — Pré-requisitos (não são pesquisa de estratégia)
1. ~~`git init`~~ **feito em 2026-09-19** (sem commits; pasta `experiments/` criada — D4). Primeiro commit autorizado e realizado em 2026-09-19.
2. Natureza da série e rollover (Q1, R6); política para lacunas (R7).
3. ~~**Correções de simulação:**~~ **feitas** (R1/R1b, R4, R8, R9, R10). Cada uma justificada como erro de modelagem ([05 §10](05_replay_trading_guide.md)), com aprovação do usuário. R2 foi tratado pela convenção de entrada a nível; R3 (Padrão 2 ambíguo: compra primeiro) e R5 (slippage também no alvo) foram **mantidos e documentados**; R7 segue em aberto.
4. ~~Premissas de execução únicas~~ **aplicadas** em `configs/wdo_default.toml` (provisórias; D6).
5. Auditoria linha a linha EA × Python e, se possível, paridade com o Strategy Tester do MT5.
6. ~~**Extrair a interface de estratégia do motor**~~ **feito**: candidatos não exigem mais editar o simulador.
7. ~~**Guarda de partições:**~~ **feita** (`wdo.partitions`); carregadores/notebooks de pesquisa recusam dados fora do conjunto permitido (holdout inacessível por construção); *lookback* de aquecimento só com partições anteriores.
8. ~~**Suíte de testes de vazamento**~~ **feita** ([05 §11](05_replay_trading_guide.md)) implementada e passando para o V0 (ela deve expor R1/R8 se forem reais).
9. ~~Estrutura do registro de experimentos~~ criada (`experiments/`); falta o modelo dos blocos de integridade e overfitting de [07 §5](07_agent_protocol.md) em `decision.md`.
10. **Motor congelado** (`ENGINE_VERSION 1.1.0` desde a D8; a 1.0.0 foi o congelamento do G0; `tests/test_engine_frozen.py`) — **feito**. **Restabelecer o Baseline V0 no conjunto de pesquisa** é o **primeiro passo da primeira run** (depois do commit do código congelado, para a proveniência apontar para ele). Deliberadamente **não** olhei o desempenho do V0 durante o G0, para o motor não ser ajustado por resultado. Os números atuais do V0 (amostra inteira, motor com R1–R5 em aberto) **não** são a referência.

### G1 — Aprovação do usuário
Aprova a metodologia e fecha D1–D7. Só então a Fase 1 começa.

### Fase 1 — Descoberta de estratégia
Ciclo de [07 §5](07_agent_protocol.md) dentro do orçamento (D2), no conjunto de pesquisa, com consultas esporádicas à validação. Saída: uma ou mais arquiteturas promissoras **congeladas**, ou o resultado "nenhum edge convincente". Sem ajuste fino de limiares.

**Lições da RUN-0001 incorporadas à metodologia (2026-09-19):** (1) o gargalo é a estrutura de saída (payoff 0,6): o V0 não é protegido e TP/SL podem ser redesenhados ([06 §1–§2](06_quant_finance_playbook.md)); (2) benchmark de entrada sem edge (placebo) obrigatório ([06 §8](06_quant_finance_playbook.md)); (3) limite de resolução estatística ([06 §12](06_quant_finance_playbook.md)); (4) rótulo de origem da hipótese e cautela com hipóteses vindas de decomposição ([06 §10](06_quant_finance_playbook.md)); (5) status BLOCKED e lacuna de capacidade de saída do motor (D8, implementada no motor 1.1.0); (6) livro de aprendizados (`experiments/knowledge.md`), checagem de novidade e fronteira atual como pai padrão ([06 §10](06_quant_finance_playbook.md)).

### G2 — Aprovação para a Fase 2
Feita pelo usuário, após relatório da Fase 1 (todos os experimentos, inclusive rejeitados).

### Fase 2 — Otimização de parâmetros
Busca sistemática de limiares, walk-forward de tuning, sensibilidade paramétrica (platôs, não picos), DSR/PBO com a contagem de trials registrada. Janelas e dados definidos no início da fase.

### G3 — Holdout e go/no-go
Uma única abertura do holdout, com estratégia congelada e autorização explícita. Em seguida: paper trading/shadow mode → go-live reduzido → escala (multi-ativo, paralelização, monitoramento de decaimento).

## Contaminação já registrada (divulgação)

Em 2026-09-18, antes de existirem fronteiras de dados, o Baseline V0 foi executado sobre **toda** a amostra (2026-01-01 → 2026-09-01) e o agente viu: métricas agregadas (138 trades, win rate 58,7%, PF 0,85, drawdown −17,1%, sem custos), split long/short e as primeiras 10 operações/20 eventos (fev/2026). Gráficos por período foram gerados em `outputs/notebooks/`, mas **não foram examinados** pelo agente. Efeito: o holdout **não é virgem para o V0**, embora o vazamento seja só agregado e o V0 seja apenas o comparador. Tratamento em D1. Esses números são diagnóstico de pipeline; nenhum agente deve usá-los para escolher hipóteses.

## Decisões metodológicas

Status (2026-09-19): **D1–D7 decididas** (D6 provisória até o usuário informar custos reais). **D8 e D9 aprovadas** (D8: implementada no motor 1.1.0; D9: em vigor). A Fase 1 segue autorizada run a run pelo usuário (G1).

- **D1 — Fronteiras pesquisa / validação / holdout. DECIDIDO em 2026-09-19 (imutáveis):** dados existentes (2026-01-02 → 2026-09-01). **Pesquisa 2026-01-02 → 2026-06-30** (efetivo fev–jun, aquecimento das EMAs D1); **validação 2026-07-01 → 2026-07-31**; **holdout 2026-08-03 → 2026-09-01**. Estimativa (ritmo do V0, ~0,8 trade/dia; depende do candidato): ~80 / ~19 / ~17 trades. Limitações aceitas: o holdout de ~1 mês é **checagem de sanidade, não prova**; a contaminação agregada do V0 continua registrada; dados a partir de 2026-09-02 ficam reservados como futuro.
- **D2 — Orçamento de pesquisa. DECIDIDO: por tempo.** Cada prompt-task define X minutos; regras em [07 §6](07_agent_protocol.md). Salvaguardas mantidas como propostas (a confirmar): máx. 2 refinamentos por linhagem; encerrar uma família após 2 rejeições seguidas; consultas à validação limitadas (≤ 3 no total). Todo experimento conta como trial.
- **D3 — Critérios de aceitação e rejeição. DECIDIDO (mecanismo): placar top 3 de sobrevivência**, global entre runs ([06 §5](06_quant_finance_playbook.md)); "melhor" é ordinal (portões → dominância → desempate conservador), pois a Fase 1 não usa função numérica com pesos. **Limiares dos portões APROVADOS em 2026-09-19** (fixos, antes da primeira run): ≥ 30 trades no conjunto de pesquisa; drawdown máximo ≤ 15% do capital; os 5 melhores trades ≤ 40% do lucro bruto; nenhum mês com mais de 40% do lucro total; expectância > 0 após custos.
- **D4 — Armazenamento e proveniência. DECIDIDO e feito em 2026-09-19:** `git init`, primeiro commit autorizado, e `experiments/` com um subdiretório por prompt-task ([07 §4](07_agent_protocol.md), `experiments/README.md`). O registro de uma run é commitado **uma vez, ao fim do prompt-task** (não por experimento).
- **D5 — Escopo do G0. APROVADO e IMPLEMENTADO em 2026-09-19:** correção das EMAs (R1), separação estratégia/simulador, convenção de entrada (R8) e barra de entrada (R9). Convenção adotada: entrada no `open` só é válida quando (i) o sinal vem de barras já **fechadas** (ex.: IFR de P4, referência de barras anteriores) ou (ii) o próprio `open` já satisfaz o gatilho (gap além do nível). Se o gatilho depende do `high/low` da barra corrente, a entrada ocorre **no nível do gatilho** (ou no `open`, se este já passou do nível), sempre com slippage contra e **dentro do range OHLC** da barra; depois da entrada, stop/alvo da própria barra são avaliados com ordem **adversa** (stop primeiro se ambos couberem). Teste de aceitação: mutação da mesma barra ([05 §11](05_replay_trading_guide.md)). Revisão de R2–R5 e R7 segue no G0.
- **D6 — Premissas de execução únicas. DECIDIDO (provisório; confirmado em 2026-09-19): valores comuns de mercado até o usuário informar os exatos.** Cenário base provisório (**placeholders não verificados junto à B3/corretora; substituir quando os valores reais chegarem**): valor do ponto R$ 10; slippage 0,5 pt por lado (entrada e saída); custos totais R$ 1,00 por contrato por lado. Efeito em pontos por trade: `c ≈ 1,0 (slippage) + 0,2 (custos) = 1,2` ⇒ win rate de equilíbrio com alvo 6 / stop 10 ≈ `(10 + 1,2) / 16 = 70%` (62,5% sem custos). Rodar a grade de sensibilidade de execução (slippage 0 / 0,5 / 1 pt) para todos os candidatos. Aplicar em `configs/` no G0; ao chegar o valor real, o V0 e o placar são reexecutados. Gap além do stop (R4) e slippage no alvo (R5): tratamento conservador, a implementar no G0.
- **D7 — Regimes e janelas. DECIDIDO em 2026-09-19 (delegado ao agente, calibrado para amostra pequena):** 2 grupos por dimensão, avaliados isoladamente, janela móvel de 20 pregões, grupo com < 15 trades é inconclusivo. Definições em [06 §11](06_quant_finance_playbook.md).
- **D8 — Capacidade de saída do motor. APROVADA e IMPLEMENTADA em 2026-09-19 (motor 1.1.0; tarefa separada de qualquer experimento; aguarda commit autorizado pelo usuário).** O motor 1.0.0 só tem stop/alvo em pontos fixos do `Config` ([05 §10](05_replay_trading_guide.md)). Proposta: motor 1.1.0 em que a estratégia devolva, por entrada, uma especificação de saída (preço de stop, alvo opcional, saída por horário, trailing opcional), com a **mesma semântica conservadora** (gap, hipótese adversa, barra de entrada), testes novos e regressão que prove que o V0 continua idêntico bit a bit; depois, reexecutar V0 e candidatos. Desbloqueia saídas adaptativas/por estrutura, time-stop e hipóteses de fim de dia. Direção aprovada: saídas **adaptativas** (ex.: ATR) e por estrutura. Implementada como `ExitSpec` ([05 §10](05_replay_trading_guide.md)); o V0 ficou idêntico bit a bit (testes de regressão e comparação 1.0.0 × 1.1.0 nos dados de pesquisa), então o baseline EXP-0000 da RUN-0001 continua válido.
- **D9 — Classificação de regras do V0 como desenho. APROVADA em 2026-09-19 (o usuário quer o sistema mais livre).** Janela de sessão (09:00–10:30) e limite de 1 trade/dia tratados como **escolhas de desenho** (desafiáveis com hipótese; outras janelas do dia e mais de um trade por dia, inclusive em horário específico, são permitidos; trades no mesmo dia são correlacionados e não contam como amostras independentes), aplicados pelo motor de forma consistente; tamanho da posição fixo em 1 contrato. Os pressupostos de simulação (custos, slippage, política intrabar, execução conservadora, partições) seguem protegidos.

## Perguntas em aberto para o usuário

- **Q1.** A série `data/raw/wdo_data.csv` é contínua ajustada? Como foi gerada (ferramenta, critério de rollover)?
- **Q2.** Valor do ponto e custos reais (corretagem, emolumentos B3, slippage típico na abertura) na Genial?
- **Q3.** O EA está rodando ao vivo? Existem logs/relatórios do Strategy Tester ou operações reais para comparação de paridade?
- **Q4.** Preferência de estrutura final: pacote `src/` com CLI, ou notebooks + módulo?
- **Q5.** Há acesso a dados M1 ou ticks/bid-ask do WDO para modelar toque de EMA e slippage?
- **Q6.** Meta de negócio: uso pessoal ou gestão de capital de terceiros (regulatório)?
- **Q7.** O projeto deve permanecer local ou integrar Databricks (a pasta se chama `Databricks_dev`)?
- **Q8.** Aceita adotar git e um fluxo de branches por agente?
