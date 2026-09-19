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

**Baseline V0 é uma referência, não uma restrição.** É a estratégia atual (EA v1.35 replicado) e serve como referência reproduzível, comparador dos candidatos, hipótese inicial e implementação conhecida. **Não** é uma estratégia ótima.

- **Preservar:** a implementação do V0, seus resultados, a reprodutibilidade e a proveniência (nunca é sobrescrita; [07 §4](07_agent_protocol.md)) e a semântica de execução do motor congelado.
- **Não proteger por padrão:** regras de entrada e saída, TP 6 / SL 10 e a relação risco/retorno, escolha de indicadores, limiares (IFR, EMAs, offset do canal), janela de sessão, limite de 1 trade/dia, filtros e a suposição de quais componentes são úteis. Tudo isso pode ser desafiado ou substituído na Fase 1 com uma hipótese clara (mercado, gestão de risco, estatística, execução ou robustez). Candidatos nunca sobrescrevem o V0, mas podem diferir muito dele.
- **O que continua protegido** é a *integridade da simulação* (cronologia, sem look-ahead, execução conservadora, custos e slippage, partições de dados, versão do motor), não o desenho da estratégia. A lista exata está em [05 §10](05_replay_trading_guide.md). Tornar esses pressupostos de simulação flexíveis "para melhorar o resultado" continua sendo p-hacking.

A pergunta central da Fase 1 é: **"que lógica de trading parece capaz de produzir um edge robusto, repetível e de risco controlado?"** — e não "que combinação de regras dá o maior retorno histórico?". O agente tenta **falsificar** ideias fracas; não força o backtest a ficar lucrativo. "Nenhum edge convincente" é um resultado de pesquisa válido.

## 2. Duas fases distintas

| | **Fase 1 — Descoberta de estratégia** | **Fase 2 — Otimização de parâmetros** |
|---|---|---|
| Pergunta | Qual arquitetura/lógica tem edge robusto? | Que regiões de parâmetros tornam *essa arquitetura* mais robusta? |
| Permitido | Mudanças **estruturais** com hipótese clara, incluindo a arquitetura de risco e grandes mudanças de parâmetro ou de forma funcional que testem uma hipótese distinta (stop/alvo fixos → adaptativos, relação risco/retorno, limiar fixo → normalizado pela volatilidade): lógica de entrada/saída, trend-following vs. mean-reversion, detecção de regime, filtros de volatilidade/momentum, níveis do dia anterior, comportamento da abertura, famílias de sinal (IFR ou outras), combinação de sinais independentes, filtros de *não operar*, filtros de sessão/condição de mercado | Busca sistemática de limiares, hiperparâmetros, walk-forward de tuning, análise de sensibilidade paramétrica |
| Proibido | **Busca numérica local** (hill-climbing) e busca exaustiva: TP 6→6,5→7, multiplicador de ATR 1,0→1,1→1,2, IFR 14→13, escolhidos porque melhoram o histórico. Isso é Fase 2 | Começar antes de existir ≥1 arquitetura promissora aprovada pelo usuário |
| Dados | Conjunto de pesquisa (livre) + validação (esporádica) | Definido no início da fase, com aprovação |
| Início | Somente após aprovação explícita do usuário (portão em [08](08_roadmap_and_open_questions.md)) | Somente após conclusão da Fase 1 e nova aprovação |

**Mudança estrutural de parâmetros (Fase 1) × otimização (Fase 2).** A Fase 1 **pode** mudar parâmetros de forma substancial quando isso é necessário para testar uma hipótese diferente. Exemplos válidos: stop fixo → stop adaptativo à volatilidade (ATR); alvo fixo → alvo por estrutura de mercado; relação risco/retorno assimétrica ↔ simétrica; saídas de distância fixa → saídas em ATR; arquiteturas de saída diferentes por regime; remover um indicador cuja lógica parece desnecessária; limiar fixo → quantidade normalizada ou relativa à volatilidade. São experimentos de *desenho* de estratégia. Exemplo já feito: o EXP-0003 da RUN-0001 levou o alvo de 6 para 20 pontos como hipótese sobre a estrutura de payoff.

**Regra operacional (verificável):**
1. Para uma hipótese, testa-se **uma** alternativa (valor ou forma funcional) escolhida *a priori* pelo racional e registrada **antes** de rodar; não se varre uma faixa.
2. Dentro de uma linhagem, re-testar **vizinhos** de um valor já testado do mesmo parâmetro só é permitido com um **mecanismo novo** (nova hipótese). Sem isso é hill-climbing (Fase 2).
3. Antes de mudar qualquer parâmetro existente, registrar: (i) por que a suposição atual pode ser estruturalmente inadequada; (ii) que comportamento alternativo está sendo testado; (iii) por que a mudança é materialmente diferente; (iv) que resultado sustentaria ou rejeitaria a hipótese. Ordem: hipótese → mudança estrutural → replay → avaliação; **nunca** observar → ajustar → observar → ajustar até as métricas melhorarem.

**Estratégias adaptativas são candidatas válidas, não superiores por construção.** O comportamento pode depender de condições observáveis point-in-time (ATR, volatilidade realizada, range de abertura, range recente, força de tendência, momentum, distância a níveis do dia anterior, regime), calculadas só com barras fechadas, **no lado da estratégia** (não no motor congelado) e cobertas pelos testes de vazamento ([05 §5, §11](05_replay_trading_guide.md)). Todo candidato adaptativo é comparado com a sua **contraparte fixa** (ablação/controle) e só é mantido se os graus de liberdade extras melhorarem materialmente robustez (ver disciplina de complexidade, §5). Cada multiplicador ou limiar de um componente adaptativo **conta** como parâmetro.

Pergunta central da Fase 1: **"que combinação de lógica de trading, arquitetura de risco e comportamento adaptativo parece capaz de produzir um edge robusto e repetível?"**, e não "quais ajustes numéricos vizinhos maximizam o backtest?". O agente tem ampla liberdade de redesenho e disciplina estrita contra curve fitting.

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

Comparação entre candidatos é por **dominância e trade-offs explícitos** contra o Baseline V0, contra a **fronteira atual** (pai padrão, ver §10) e entre si, dimensão a dimensão (ver critérios em [07 §5](07_agent_protocol.md)), não por ranking de um número.

**Placar top 3 (sobrevivência).** A pesquisa mantém um placar global com os **3 melhores experimentos**: um experimento que passa nos portões e é melhor, dados os objetivos, entra no top 3 e o pior sai (a saída é do placar, nunca do registro). Como a Fase 1 **não tem função de otimização numérica com pesos**, "melhor" é ordinal:
1. **Portões** (eliminatórios): integridade e revisão de overfitting limpas ([07 §5](07_agent_protocol.md)); não frágil ([§11](#11-robustez-temporal-e-concentração-de-pnl)); amostra mínima; critério absoluto (expectância positiva após custos), pois vencer o V0 é um piso baixo. **Limiares aprovados (D3, 2026-09-19), fixos antes da primeira run:** ≥ 30 trades no conjunto de pesquisa; drawdown máximo ≤ 15% do capital inicial; os 5 melhores trades ≤ 40% do lucro bruto; nenhum mês com mais de 40% do lucro total; expectância > 0 após custos.
2. **Dominância** nas seis dimensões de [§3](#3-framework-de-qualidade-multi-objetivo-sem-score-sintético): A é melhor que B se não for pior em nenhuma dimensão material e for melhor em ao menos uma.
3. **Desempate conservador** (lexicográfico, sem pesos) quando nenhum domina o outro: (i) cauda e drawdown; (ii) estabilidade e concentração de PnL; (iii) Profit Factor com nº de trades; (iv) win rate com payoff; (v) PnL.

**Viés de seleção:** um torneio sobre o mesmo conjunto de pesquisa produz vencedores otimistas (*winner's curse*): quanto mais experimentos, maior a chance de o top 3 refletir sorte. Por isso todo experimento conta como trial, o placar é julgado só no conjunto de pesquisa, e apenas o top 3 é elegível à validação (consultas limitadas, [§6](#6-política-de-dados)). Espera-se degradação na validação; ela é o teste, não um erro.

**Disciplina de complexidade: complexidade adicional precisa merecer seu lugar.** Um candidato mais complexo só é preferido se a lógica adicional melhorar **materialmente** robustez, drawdown, estabilidade, consistência ou comportamento de cauda; melhora marginal nas métricas históricas não justifica complexidade substancial. Com desempenho amplamente comparável, preferir a estratégia mais simples. Evitar "estratégias Frankenstein": regras empilhadas porque cada uma melhorou um pouco o backtest. Toda regra adicionada tem hipótese própria e é avaliada por **ablação** (remover a regra e comparar); se o resultado não piora de forma material, a regra sai. **Contabilidade de complexidade:** todo candidato declara seu número de parâmetros de desenho livres (graus de liberdade) e a premissa do V0 que desafia; entre desempenhos semelhantes, vence a arquitetura com menos graus de liberdade. Sofisticação não é qualidade.

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
- fazer busca numérica local (hill-climbing) em parâmetros, ou re-testar vizinhos de um valor já testado sem mecanismo novo (regra operacional da §2), porque melhoram o resultado histórico;
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

**Benchmark de entrada sem edge (obrigatório na Fase 1).** Numa caminhada sem drift, a probabilidade de atingir o alvo `G` antes do stop `L` é `L/(G+L)`; com custo `c` a expectativa de uma entrada *sem* edge é `−c` por trade. No V0 (G=6, L=10): ~62,5% de acerto e ~−R$ 12 por trade. Como o benchmark depende da estrutura de saída, **todo experimento reporta o excesso sobre um placebo**: entradas com direção aleatória, nos mesmos instantes, com a **mesma arquitetura de saída, custos e slippage** (sementes fixas, vários sorteios). Um candidato só tem "edge" se superar a distribuição do placebo com folga maior que o ruído amostral (§12). Lição da RUN-0001: os 8 candidatos ficaram perto do benchmark.

## 9. Gestão de risco

- **Por trade:** stop fixo; tamanho definido por risco, não convicção. **Por dia/estratégia:** stop diário de perda e limite de drawdown que aciona revisão/desligamento.
- **Kelly:** só fracionário (≤ ¼) e com estimativas robustas.
- **Risco de ruína:** Monte Carlo/bootstrap das sequências de trades para P(drawdown > X).
- **Cauda:** WDO em eventos (Copom, payroll, política) salta; medir a distribuição real de perdas vs. o stop nominal.
- **Várias estratégias:** alocar por risco (volatility targeting/risk parity), não por capital.

## 10. Geração de hipóteses (Fase 1)

- **Origem da hipótese** (rótulo obrigatório): *literatura*, *mecanismo de mercado* ou *decomposição* (do V0 ou de um candidato no conjunto de pesquisa). Decompor para formular hipóteses é permitido, mas a hipótese vinda de decomposição é **data-informed**: precisa ser rotulada como tal, nunca é promovida nem levada a um checkpoint de validação sem essa ressalva, e deve ser reforçada por um mecanismo independente. Preferir literatura e mecanismo. (Na RUN-0001, os EXP-0001/0004/0005/0006/0007 nasceram de decomposição.)
- Cada hipótese tem **racional de mercado** (quem está do outro lado? por que o edge deveria existir?) antes do código. Exemplos válidos: abertura com forte momentum torna trades de fade menos atraentes; aberturas de baixa volatilidade favorecem reversão à média; certos níveis do dia anterior funcionam como referências de liquidez; filtros direcionais reduzem trades contra-tendência estruturalmente ruins.
- Decompor o V0 **no conjunto de pesquisa** por padrão (P1–P4), direção, dia da semana, faixa de IFR, distância ao PDH/PDL, gap, volatilidade do dia anterior é diagnóstico para *formular* hipóteses, não para escolher limiares.
- Microestrutura: a abertura tem spread e volatilidade atípicos; o modelo de custo da abertura difere do meio do dia.
- Features de ML, se surgirem: point-in-time, defasagem explícita, teste de vazamento.

### Aprendizado cumulativo ("sempre melhorando")

A pesquisa acumula conhecimento e **não desce de nível**: não re-testa o que já foi testado e claramente não entregou resultado melhor, sem uma boa razão. Não é uma regra agressiva; é um registro, em uma linha, do porquê.

1. **Livro de aprendizados** (`experiments/knowledge.md`): para cada hipótese/família, veredito, evidência, **condições do teste** (versão do motor, custos, arquitetura de saída, partição, amostra) e **condição de reabertura**. Atualizado ao fim de cada run; nunca se apagam linhas (nova evidência = nova linha datada). Um resultado só vale nas condições em que foi obtido.
2. **Vereditos distintos:** REFUTADO (pior que o benchmark de zero edge com folga, ≳ 2 erros-padrão, amostra adequada) · NÃO SUSTENTADO (sem excesso demonstrável) · INCONCLUSIVO (amostra ou desenho insuficientes, ex.: < 30 trades) · BLOCKED/INVÁLIDO · PROMISSOR (data-informed). Com ≤ ~100 trades quase nada é "refutado": não confundir "não sustentado" com "provado sem edge".
3. **Checagem de novidade (antes de cada experimento):** consultar o livro. Se a hipótese, ou algo materialmente equivalente, já foi testada, o experimento só prossegue com um **motivo de reabertura** registrado: (i) **mecanismo novo** (ex.: capacidade do motor que antes não existia); (ii) **premissa alterada** (custos reais, série corrigida); (iii) **evidência inconclusiva** refeita com melhor desenho; (iv) **checkpoint de validação** planejado. Reabrir vizinhos numéricos de um valor já testado continua proibido sem mecanismo novo (§2).
4. **Fronteira atual como pai padrão:** vencer o V0 é um piso baixo. Por padrão o pai de um novo experimento é o melhor candidato da fronteira atual (o V0 só quando a hipótese é sobre ele) e o resultado é comparado com o V0, com o pai e com o placebo. Cada experimento deve **elevar** a fronteira, ou explicar o que ensina.
5. **Ressalvas:** o degrau que sobe também acumula snooping na mesma partição; a contagem cumulativa de tentativas é reportada em toda run e nada é promovido sem checkpoint de validação. A exploração de famílias diferentes (30–40% do esforço) continua obrigatória para o "sempre melhorando" não virar máximo local.

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

- **Limite de resolução:** o erro-padrão do win rate é `sqrt(p(1−p)/n)`: com ≤ ~100 trades é ~5 p.p. Diferenças menores que ~2 erros-padrão (win rate, expectância, comparação com o placebo) **não são evidência**; declarar isso na avaliação.
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
