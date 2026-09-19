# 06 — Playbook de quant finance: metodologia de pesquisa

Este documento define **como a pesquisa é conduzida e como estratégias são julgadas**. Regras de simulação: [05](05_replay_trading_guide.md). Comportamento do agente, ciclo de experimentos e orçamento: [07](07_agent_protocol.md). Fases, portões e decisões pendentes: [08](08_roadmap_and_open_questions.md).

## 1. Papel e prioridades

O agente atua como **pesquisador quant / systematic trader profissional**, não como otimizador. Prioridades, em ordem de desempate:

1. correção sobre esperteza;
2. robustez sobre retorno histórico máximo;
3. reprodutibilidade sobre experimentação ad hoc;
4. premissas de execução conservadoras sobre otimistas;
5. hipóteses explícitas sobre tentativa e erro cega;
6. consistência ajustada ao risco sobre alto risco/alto retorno.

**Baseline V0** é a estratégia atual (EA v1.35 replicado). É o ponto de partida e o comparador de todos os candidatos; **não** é um desenho que precise ser preservado. Ela nunca é sobrescrita (ver [07 §4](07_agent_protocol.md)).

A pergunta central da Fase 1 é: **"que lógica de trading parece capaz de produzir um edge robusto, repetível e de risco controlado?"** — e não "que combinação de regras dá o maior retorno histórico?". O agente tenta **falsificar** ideias fracas; não força o backtest a ficar lucrativo. "Nenhum edge convincente" é um resultado de pesquisa válido.

## 2. Duas fases distintas

| | **Fase 1 — Descoberta de estratégia** | **Fase 2 — Otimização de parâmetros** |
|---|---|---|
| Pergunta | Qual arquitetura/lógica tem edge robusto? | Que regiões de parâmetros tornam *essa arquitetura* mais robusta? |
| Permitido | Mudanças **estruturais** com hipótese de mercado: lógica de entrada/saída, trend-following vs. mean-reversion, detecção de regime, filtros de volatilidade/momentum, níveis do dia anterior, comportamento da abertura, famílias de sinal (IFR ou outras), combinação de sinais independentes, filtros de *não operar*, filtros de sessão/condição de mercado | Busca sistemática de limiares, hiperparâmetros, walk-forward de tuning, análise de sensibilidade paramétrica |
| Proibido | Ajuste fino de limiares e busca exaustiva. Trocar IFR 14 por 13 ou stop 10 por 9,5 **não** é descoberta, salvo hipótese estrutural clara | Começar antes de existir ≥1 arquitetura promissora aprovada pelo usuário |
| Dados | Conjunto de pesquisa (livre) + validação (esporádica) | Definido no início da fase, com aprovação |
| Início | Somente após aprovação explícita do usuário (portão em [08](08_roadmap_and_open_questions.md)) | Somente após conclusão da Fase 1 e nova aprovação |

**Estrutural × micro-ajuste (Fase 1).** Preferir: mudar a arquitetura de entrada ou de saída; introduzir ou remover uma família de sinal; separar regimes de mercado; comportamento dependente de volatilidade; lógica de momentum × reversão à média; filtros de *não operar*. Evitar microvariações (IFR 14→13, stop 10→9,5, EMA 17→18) **salvo** se necessárias para testar uma hipótese estruturalmente diferente — e então o que se registra é a hipótese estrutural. Ajuste fino de parâmetros é Fase 2.

Execução: **sensibilidade de execução** (slippage, custos, `intrabar_policy`, atraso de entrada) é teste de robustez, não otimização, e vale nas duas fases — ver §6.

## 3. Framework de qualidade (multi-objetivo, sem score sintético)

```
Qualidade = f( Profit Factor, Win Rate, Drawdown, Estabilidade, Nº de trades, Consistência do PnL )
```

É um **arcabouço conceitual**, não uma função numérica. **Não atribuir pesos, não construir nem otimizar um score sintético** na Fase 1. Serve para que nenhuma estratégia seja julgada por uma métrica de destaque isolada.

| Dimensão | Como interpretar |
|---|---|
| **Profit Factor** | Desejável alto, mas sempre lido com nº de trades, estabilidade temporal, drawdown e concentração de lucro. PF muito alto com poucos trades **não** é evidência de robustez. |
| **Win Rate** | Nunca isolado de payoff e distribuição de perdas. Win rate alto com perda média péssima pode ser pior que win rate menor com payoff assimétrico (ver §8: com alvo 6 / stop 10 o equilíbrio é 62,5%). |
| **Drawdown** | Avaliar **magnitude e duração/persistência**. Penalizar fortemente estratégias capazes de grande destruição de capital, mesmo com PnL histórico alto. |
| **Estabilidade** | Comportamento razoável entre períodos e condições de mercado; sem dependência excessiva de um único regime. |
| **Nº de trades** | Amostra suficiente para sustentar conclusões. Métricas impressionantes com poucos trades não são evidência forte. |
| **Consistência do PnL** | Como o lucro se distribui no tempo. Preferir PnL espalhado à dominância de poucos trades/dias extraordinários. |

## 4. Diagnósticos de apoio

Interpretam as dimensões acima; não são objetivos por si:

payoff ratio, ganho médio, perda média, expectância, máx. perdas e ganhos consecutivos, **eventos de cauda negativa**, performance mensal e rolante, duração dos trades, long vs. short, **contribuição dos melhores trades e dos melhores dias para o PnL total**, tempo de recuperação após drawdowns. Cauda, assimetria de payoff e concentração de PnL são diagnósticos de primeira classe.

> **Regra geral: nenhuma métrica é interpretada sem seu contexto estatístico e temporal.**
> Profit Factor + nº de trades · Win Rate + payoff · PnL + drawdown · Retorno + concentração de PnL · Performance + estabilidade temporal.
>
> **Robustez antes de otimização.** Uma estratégia que só funciona sob um conjunto estreito de condições históricas não é evidência forte na Fase 1.

## 5. Preferência por robustez

O objetivo **não** é PnL, Profit Factor, win rate ou retorno máximos. Preferir candidatos equilibrados: um retorno um pouco menor com drawdown materialmente menor, PnL mais estável, distribuição de trades mais ampla e menos risco de cauda **é preferível** a um retorno muito maior com risco frágil.

Perfil desejado: downside controlado; crescimento estável do capital; frequência de trades razoável; Profit Factor robusto; relação saudável win rate × payoff; baixa dependência de outliers; baixa probabilidade de dano severo ao capital.

Comparação entre candidatos é por **dominância e trade-offs explícitos** contra o Baseline V0 e entre si, dimensão a dimensão (ver critérios em [07 §5](07_agent_protocol.md)), não por ranking de um número.

**Placar top 3 (sobrevivência).** A pesquisa mantém um placar global com os **3 melhores experimentos**: um experimento que passa nos portões e é melhor, dados os objetivos, entra no top 3 e o pior sai (a saída é do placar, nunca do registro). Como a Fase 1 **não tem função de otimização numérica com pesos**, "melhor" é ordinal:
1. **Portões** (eliminatórios): integridade e revisão de overfitting limpas ([07 §5](07_agent_protocol.md)); não frágil ([§11](#11-robustez-temporal-e-concentração-de-pnl)); amostra mínima; critério absoluto (expectância positiva após custos), pois vencer o V0 é um piso baixo. **Limiares aprovados (D3, 2026-09-19), fixos antes da primeira run:** ≥ 30 trades no conjunto de pesquisa; drawdown máximo ≤ 15% do capital inicial; os 5 melhores trades ≤ 40% do lucro bruto; nenhum mês com mais de 40% do lucro total; expectância > 0 após custos.
2. **Dominância** nas seis dimensões de [§3](#3-framework-de-qualidade-multi-objetivo-sem-score-sintético): A é melhor que B se não for pior em nenhuma dimensão material e for melhor em ao menos uma.
3. **Desempate conservador** (lexicográfico, sem pesos) quando nenhum domina o outro: (i) cauda e drawdown; (ii) estabilidade e concentração de PnL; (iii) Profit Factor com nº de trades; (iv) win rate com payoff; (v) PnL.

**Viés de seleção:** um torneio sobre o mesmo conjunto de pesquisa produz vencedores otimistas (*winner's curse*): quanto mais experimentos, maior a chance de o top 3 refletir sorte. Por isso todo experimento conta como trial, o placar é julgado só no conjunto de pesquisa, e apenas o top 3 é elegível à validação (consultas limitadas, [§6](#6-política-de-dados)). Espera-se degradação na validação; ela é o teste, não um erro.

**Disciplina de complexidade: complexidade adicional precisa merecer seu lugar.** Um candidato mais complexo só é preferido se a lógica adicional melhorar **materialmente** robustez, drawdown, estabilidade, consistência ou comportamento de cauda; melhora marginal nas métricas históricas não justifica complexidade substancial. Com desempenho amplamente comparável, preferir a estratégia mais simples. Evitar "estratégias Frankenstein": regras empilhadas porque cada uma melhorou um pouco o backtest. Toda regra adicionada tem hipótese própria e é avaliada por **ablação** (remover a regra e comparar); se o resultado não piora de forma material, a regra sai.

## 6. Política de dados

O histórico é dividido **por tempo** (nunca aleatoriamente) em três conjuntos. As fronteiras exatas **exigem aprovação explícita antes da Fase 1** (decisão D1 em [08](08_roadmap_and_open_questions.md)) e, uma vez fixadas, não mudam.

| Conjunto | Uso |
|---|---|
| **Pesquisa / desenvolvimento** | Livre durante a Fase 1: gerar hipóteses, diagnósticos, comparar candidatos. |
| **Validação** | Testa periodicamente se uma hipótese **generaliza** além da amostra de desenvolvimento. **Não** consultar a cada experimento trivial; cada consulta é registrada e consome orçamento ([07 §6](07_agent_protocol.md)). |
| **Holdout final** | **Invisível na Fase 1.** O agente não pode inspecionar, resumir, calcular métricas, otimizar contra ele, usá-lo para aceitar/rejeitar hipóteses **nem usar informação dele indiretamente** ao desenhar candidatos. Só é aberto **uma vez**, com estratégia congelada e autorização explícita do usuário. |

**Validação usada repetidamente vira dado de treino.** Cada consulta cujo resultado influencia uma decisão é otimização indireta: após várias consultas, a validação deixou de medir generalização. Consultas são raras, registradas com motivo e candidato, e contam como trials. O holdout não influencia o desenho de nenhuma forma, nem indireta.

Consequências operacionais: (a) carregadores e notebooks de pesquisa devem receber as fronteiras da configuração e **recusar** dados fora do conjunto permitido (o *lookback* de aquecimento de indicadores pode usar partições **anteriores**, nunca posteriores); (b) plots/estatísticas de série completa são proibidos durante a Fase 1; (c) achados de regime ou calendário observados no holdout, mesmo de relance, contaminam o candidato.

**Aviso de contaminação existente:** o Baseline V0 já foi executado sobre a amostra inteira antes de as fronteiras existirem (métricas agregadas, split long/short e as primeiras 10 operações de fev/2026 foram vistas em 2026-09-18). Ver tratamento em [08](08_roadmap_and_open_questions.md) (D1). Esses números são **diagnóstico de pipeline, não referência de pesquisa**.

**Limite de amostra:** ~7 meses úteis (o primeiro trade só ocorre após o aquecimento das EMAs D1) com ~0,8 trade/dia observado no V0 tornam qualquer partição em três muito pobre em poder estatístico. Isso é uma restrição da pesquisa, a ser tratada (mais dados, dado futuro como holdout), não ignorada.

## 7. Salvaguardas contra mineração de backtest

O agente **não deve**:

- ajustar regras repetidamente contra o **mesmo** conjunto inteiro;
- continuar experimentando até "aparecerem" boas métricas;
- selecionar estratégias só por maximizarem o PnL histórico;
- alterar repetidamente pequenos limiares porque melhoram o resultado histórico;
- adicionar regras sem hipótese de mercado prévia;
- acumular regras em estratégias cada vez mais complexas sem justificativa (ver disciplina de complexidade, §5);
- consultar a validação depois de cada experimento;
- usar o holdout durante a pesquisa;
- alterar silenciosamente premissas de execução;
- modificar o motor de replay para a estratégia parecer melhor (mudança de motor só como correção de simulação, ver [05 §10](05_replay_trading_guide.md));
- apagar experimentos ruins;
- reportar seletivamente só os candidatos bem-sucedidos.

**Fase 1 é descoberta de estratégia, não mineração de métricas históricas.** Todo experimento segue **hipótese → implementação → teste → resultado**; nunca **resultado → explicação inventada depois**. Uma explicação posterior a um resultado é uma hipótese *nova*: exige novo teste sobre dados que não a inspiraram, e hipótese e racional são registrados **antes** de rodar ([07 §4](07_agent_protocol.md)).

Contrapartes obrigatórias: **contagem de tentativas** (todo experimento e toda consulta à validação conta como trial) para correções de múltiplos testes; **orçamento finito** ([07 §6](07_agent_protocol.md)); **registro imutável** de todos os experimentos, incluindo os rejeitados.

## 8. Economia do trade (sempre checar)

Para alvo `G`, stop `L`, win rate `p`, custo por trade `c` (pontos):

```
Expectativa = p·G − (1−p)·L − c          Win rate de equilíbrio p* = (L + c) / (G + L)
```
No V0 (G=6, L=10): `p* = 62,5%` sem custo; cada ponto de custo eleva `p*` em `1/16 ≈ 6,25 p.p.`. Estratégias com payoff < 1 vivem de alta taxa de acerto e são muito sensíveis a custo, slippage e stops que "escorregam" (gap além do stop). Sempre comparar `p` observado (com IC) a `p*`.

## 9. Gestão de risco

- **Por trade:** stop fixo; tamanho definido por risco, não convicção. **Por dia/estratégia:** stop diário de perda e limite de drawdown que aciona revisão/desligamento.
- **Kelly:** só fracionário (≤ ¼) e com estimativas robustas.
- **Risco de ruína:** Monte Carlo/bootstrap das sequências de trades para P(drawdown > X).
- **Cauda:** WDO em eventos (Copom, payroll, política) salta; medir a distribuição real de perdas vs. o stop nominal.
- **Várias estratégias:** alocar por risco (volatility targeting/risk parity), não por capital.

## 10. Geração de hipóteses (Fase 1)

- Cada hipótese tem **racional de mercado** (quem está do outro lado? por que o edge deveria existir?) antes do código. Exemplos válidos: abertura com forte momentum torna trades de fade menos atraentes; aberturas de baixa volatilidade favorecem reversão à média; certos níveis do dia anterior funcionam como referências de liquidez; filtros direcionais reduzem trades contra-tendência estruturalmente ruins.
- Decompor o V0 **no conjunto de pesquisa** por padrão (P1–P4), direção, dia da semana, faixa de IFR, distância ao PDH/PDL, gap, volatilidade do dia anterior é diagnóstico para *formular* hipóteses, não para escolher limiares.
- Microestrutura: a abertura tem spread e volatilidade atípicos; o modelo de custo da abertura difere do meio do dia.
- Features de ML, se surgirem: point-in-time, defasagem explícita, teste de vazamento.

## 11. Robustez temporal e concentração de PnL

Candidatos **não** são avaliados só por métricas agregadas. Onde praticável, inspecionar se o desempenho se distribui razoavelmente no tempo: resultados **mensais**; **janelas móveis**; períodos de drawdown (início, profundidade, duração, recuperação); **regimes de volatilidade**; **regimes direcionais** (alta/baixa/lateral). **Definições fixas (D7, calibradas para amostra pequena; usam só informação point-in-time e foram fixadas antes de olhar resultados):**
- **Regime de volatilidade — 2 grupos:** range do dia anterior (PDH−PDL) acima ou abaixo da mediana dos 20 pregões anteriores.
- **Regime direcional — 2 grupos:** retorno acumulado dos 5 pregões até o fechamento anterior, positivo ou negativo.
- **Janela móvel:** 20 pregões. **Recorte temporal:** mensal.
- Cada dimensão é reportada **isoladamente** (nunca cruzada) para não fragmentar os poucos trades disponíveis; grupo com menos de 15 trades é **inconclusivo**.
- São diagnósticos de robustez, **não alvos de ajuste**. Mudar estas definições exige aprovação do usuário. Um candidato pode propor seu próprio filtro de regime como hipótese estrutural (point-in-time), sem alterar estas definições de avaliação.

Avaliar explicitamente se o desempenho depende demais de: **poucos trades; poucos dias; um único mês; um único regime.** Diagnósticos: contribuição dos melhores *k* trades e dos melhores *k* dias ao PnL total; concentração mensal do PnL; eventos de cauda negativa; tempo de recuperação após drawdowns. **Teste de fragilidade:** recomputar as métricas removendo os melhores *k* trades/dias; se o edge desaparece, a estratégia é frágil.

Tratar como **frágil** a estratégia cuja rentabilidade se concentra em um período histórico estreito ou cuja maior parte do edge vem de pouquíssimos outliers. Um candidato frágil **não** é KEEP, mesmo com métricas agregadas fortes. Limiares numéricos (valor de *k*, participação máxima aceitável): D3.

## 12. Estatística para amostras pequenas

- Poucos trades → **IC largos**: bootstrap por bloco (preserva autocorrelação), testes não paramétricos.
- **Múltiplos testes:** cada variante consome graus de liberdade; corrigir (Bonferroni/Holm, DSR, Reality Check/SPA) usando a contagem de trials registrada.
- Desconfiar de Sharpe > 2–3 em backtest simples: investigar vazamento, custo e overfitting antes.
- Estimar quantos trades são necessários para distinguir `p` observado de `p*` com poder adequado **antes** de decidir.

## 13. Dados de qualidade institucional (o que falta)

Ticks/quotes ou ao menos M1 (toque de nível, EMAs ao vivo); calendário oficial B3 e tabela de vencimentos; metadados do instrumento por data (tick, valor do ponto, horários); fonte, versão e checksum por carga; dados brutos imutáveis.

## 14. Engenharia de produção

| Área | Prática |
|---|---|
| Código | Pacote instalável (`src/`), tipagem, lint, testes, CI |
| Config | Uma `Config` por ambiente (backtest/paper/live), mesma lógica |
| Reprodutibilidade | Lockfile, seed, hash do dado, commit em cada run |
| Experimentos | Registro imutável ([07 §4–5](07_agent_protocol.md)) |
| Execução | Idempotência, reconciliação, falhas de feed/corretora |
| Risco em tempo real | Kill switch, limites de posição/perda, validações pré-trade |
| Observabilidade | Logs estruturados, métricas (PnL, slippage, rejeições), alertas |
| Segredos | Variáveis de ambiente/cofre; nunca em código/notebook/git |
| Escala | Paralelizar varreduras (Fase 2); Parquet particionado; Spark/Databricks só se necessário |

## 15. Decaimento do alpha e governança

- Comparar continuamente live × backtest; definir **antes** o critério de desligamento; revalidar periodicamente (estratégias de abertura sofrem com mudanças de microestrutura e crowding).
- Registrar decisões (por que mudou, com qual evidência); reportar resultados negativos. **Nada aqui é recomendação de investimento**; futuros alavancados podem causar perdas superiores ao capital. Operar recursos de terceiros exige conformidade (CVM/B3).

## 16. Leitura de referência

López de Prado — *Advances in Financial Machine Learning* (purging, CPCV, DSR, PBO); Chan — *Quantitative Trading*; Carver — *Systematic Trading*; Bailey et al. — *Probability of Backtest Overfitting*; White (2000) *Reality Check*; Hansen (2005) *SPA*.
