# 07 — Protocolo para agentes (Claude Code, Codex, outros)

Objetivo: dois ou mais agentes trabalharem no mesmo projeto **sem se contradizer, sem duplicar esforço e sem degradar o rigor**. Metodologia de pesquisa: [06](06_quant_finance_playbook.md). Integridade da simulação: [05](05_replay_trading_guide.md). Fases e decisões pendentes: [08](08_roadmap_and_open_questions.md).

## 0. Portão de autorização (estado atual)

**A Fase 1 (descoberta de estratégia) NÃO está autorizada.** Enquanto o usuário não aprovar explicitamente a metodologia e as decisões D1–D7 de [08](08_roadmap_and_open_questions.md), o agente **não**: executa backtests, altera a estratégia, propõe/roda otimização de parâmetros, inicia descoberta de estratégia nem toca dados de validação/holdout. Trabalhos permitidos: correções de simulação aprovadas, testes, documentação, infraestrutura, análises pedidas pelo usuário.

## 1. Onboarding em 5 passos

1. Ler `README.md` desta pasta e [01](01_project_overview.md), [02](02_strategy_spec.md), [06](06_quant_finance_playbook.md), [08](08_roadmap_and_open_questions.md).
2. Ler `../../CLAUDE.md` (ou `../../AGENTS.md`): regras de conduta.
3. Abrir o trecho relevante de `reference/mt5/Robo_Abertura_WDO_Genial_v1.35.mq5` **antes** de tocar em qualquer regra **do V0**.
4. Rodar `pytest -q` e registrar o resultado real (linha de base de código).
5. Só então planejar a mudança.

## 2. Regras de conduta compartilhadas

- **Idioma:** conversar com o usuário em **pt-BR**. Código e identificadores seguem o padrão existente (inglês, com termos de domínio em português espelhando o EA).
- **Postura:** pesquisador quant profissional ([06 §1](06_quant_finance_playbook.md)): tenta falsificar ideias, não forçar lucro.
- **Honestidade sobre execução:** distinguir "verificado rodando" de "inferido lendo". Nunca inventar métricas. Se um teste falhou, dizer.
- **Sem surpresas:** não instalar dependências, não editar dados brutos, não commitar fora do autorizado (registro ao fim de cada run, §4), não mudar defaults conservadores, não apagar arquivos **sem pedir**.
- **Mudanças pequenas e revisáveis.** Refatoração estrutural: propor plano primeiro.
- **Fonte da verdade:** `reference/mt5/Robo_Abertura_WDO_Genial_v1.35.mq5` para regras do V0 (a fidelidade ao EA vale só para a implementação do V0, não para candidatos); `Config` para o cenário e a execução; cada candidato declara seus parâmetros de desenho em config própria, registrada no experimento; `tests/` para comportamento esperado.
- **Toda mudança em regra ou motor** → teste novo/atualizado + `pytest -q` + comparação antes/depois. Mudança de **motor** só como correção de simulação ([05 §10](05_replay_trading_guide.md)).
- **Nunca "melhorar" resultado** ajustando premissas de **simulação** (slippage, política intrabar, período, custos, regras de execução) nem modificando o motor. Isso é p-hacking. O **desenho da estratégia** (stops, alvos, indicadores, sessão, limite diário) não é premissa protegida: pode mudar com hipótese registrada antes de rodar ([06 §2](06_quant_finance_playbook.md)).

## 3. Divisão de trabalho sugerida

| Tipo de tarefa | Bom candidato | Observação |
|---|---|---|
| Auditar `.mq5` vs. Python, achar divergências | Qualquer | Registrar em 08 |
| Escrever testes (look-ahead, invariantes, golden) | Qualquer | Rodar antes/depois |
| Refatoração mecânica | Um agente por vez | Evitar edições concorrentes no mesmo arquivo |
| Implementar e avaliar candidatos (Fase 1) | Um agente por linhagem | Só após o portão da §0; registrar cada experimento |
| Decisões de premissa (custos, rollover, valor do ponto), fronteiras de dados, orçamento, critérios, congelamento do motor | **Usuário decide** | Agentes propõem e explicam trade-offs |

**Evitar edição simultânea do mesmo arquivo por dois agentes.** Sem git, isso é ainda mais arriscado → ver D4 em 08.

## 4. Baseline V0, candidatos e proveniência

- **Baseline V0** = estratégia original. Permanece **intacta e reproduzível** em todo o projeto; pesquisa autônoma nunca a sobrescreve.
- Candidatos: `Candidate 001, 002, …, N`. Cada um é rastreável a: **hipótese**, **estratégia-pai** (V0 ou outro candidato), **implementação** (versão do código/`Config`) e **resultados**. A pesquisa preserva a proveniência.
- **Registro de experimento (append-only)** — campos obrigatórios:
  `ID do experimento` · `data/agente` · `hipótese`, `racional de mercado`, `origem da hipótese` (literatura / mecanismo / decomposição) e `premissa(s) do V0 desafiada(s)` (registrados **antes** de rodar) · `pai` · `mudança implementada` (o que e onde) · `versão do motor e do código` · `conjunto de dados usado (fronteiras, hash)` · `Config completa (custos, slippage, política intrabar)` · `métricas + diagnósticos + IC` · `excesso sobre o placebo` · `graus de liberdade` (parâmetros de desenho livres) · `comparação com o Baseline V0` · `revisão de integridade` e `revisão de overfitting` (blocos da §5) · `decisão: KEEP / REJECT / REFINE` · `lições aprendidas` · `consumo de orçamento`.
- **Experimentos falhos são resultados válidos:** nunca apagar, sobrescrever nem omitir. Correções a um registro entram como nova entrada que referencia a anterior.
- **Livro de aprendizados:** `experiments/knowledge.md` (regras em [06 §10](06_quant_finance_playbook.md)). **Consultá-lo antes de cada experimento** (checagem de novidade) e **atualizá-lo ao fim da run**, sem apagar linhas (nova evidência = nova linha datada). Vale para a run seguinte só o que estiver ali.
- **Local:** `experiments/`, versionado no git (D4 decidida em 2026-09-19). **Cada prompt-task do usuário é uma run**: subdiretório `experiments/RUN-NNNN_<data>_<slug>/` com `run.md` (prompt, orçamento em minutos, início/fim, commit, versão do motor, hash e fronteiras dos dados) e uma pasta `EXP-NNNN_<slug>/` por experimento (`hypothesis.md`, `config.toml`, `metrics.json`, `decision.md`). O placar global está em `experiments/leaderboard.md`. Layout completo em `experiments/README.md`. Resultados gerados em `outputs/` **não** são o registro (é ignorado no git).
- **Commits (autorizado em 2026-09-19):** o registro da run (`run.md`, os `EXP-*` e o `leaderboard.md`) é commitado **uma única vez, ao fim do prompt-task** — um commit por run, **nunca** um commit por experimento ou por passo. Qualquer outro commit (código, docs) só a pedido do usuário. A mensagem segue o padrão do projeto e inclui a atribuição do agente.

## 5. Ciclo autônomo de pesquisa

```
hipótese → implementação → teste → resultado → decisão (KEEP / REJECT / REFINE) → próximo experimento
```
**Nunca** o inverso (resultado → explicação inventada depois): uma explicação pós-resultado é hipótese nova e precisa de novo teste ([06 §7](06_quant_finance_playbook.md)).

0. **Checagem de novidade e pai.** Consultar `experiments/knowledge.md`: a hipótese (ou uma materialmente equivalente) já foi testada? Se sim, registrar o **motivo de reabertura** (mecanismo novo, premissa alterada, evidência inconclusiva refeita, checkpoint de validação) ou **não rodar**. O **pai padrão é a fronteira atual** (melhor candidato do leaderboard/fronteira; o V0 só se a hipótese for sobre ele); comparar sempre com o V0, com o pai e com o placebo. Reportar a contagem **cumulativa** de tentativas.
1. **Hipótese primeiro**, com racional de mercado (exemplos em [06 §10](06_quant_finance_playbook.md)), origem rotulada e premissa do V0 desafiada, registrada **antes** de rodar. Sem hipótese, não há experimento. Nunca mudar a estratégia aleatoriamente para melhorar métricas históricas. Ao mudar um parâmetro existente, registrar os 4 pontos e cumprir a regra operacional de [06 §2](06_quant_finance_playbook.md) (uma alternativa a priori; sem vizinhos sem mecanismo novo).
   - **Validade do desenho:** confirmar que a hipótese é expressável no motor congelado (ver capacidade de saída em [05 §10](05_replay_trading_guide.md)). Se não for, o experimento é **BLOCKED (capacidade do motor)**: registrar e **não** rodar um proxy distorcido (lição do EXP-0008).
2. **Implementar** só a mudança estrutural necessária, sem tocar o motor de replay. **Revisão point-in-time obrigatória** para cada feature, indicador, filtro ou sinal novo:
   - responder por escrito: *"Este valor exato poderia ter sido conhecido neste exato timestamp em operação real?"*; resposta incerta ⇒ feature **insegura**, fora até verificação;
   - percorrer a tabela de vazamentos de [05 §5](05_replay_trading_guide.md);
   - rodar os testes de vazamento de [05 §11](05_replay_trading_guide.md) sobre a nova lógica quando tecnicamente praticável.
3. **Rodar** no conjunto de pesquisa, com as mesmas premissas de execução de todos os candidatos.
4. **Avaliar** as seis dimensões de [06 §3](06_quant_finance_playbook.md), os diagnósticos de [06 §4](06_quant_finance_playbook.md), robustez temporal e concentração de PnL ([06 §11](06_quant_finance_playbook.md)) e a ablação de complexidade ([06 §5](06_quant_finance_playbook.md)), sempre contra o V0. Reportar o **excesso sobre o placebo de entrada aleatória** com a mesma saída e custos ([06 §8](06_quant_finance_playbook.md)), aplicar o limite de resolução estatística ([06 §12](06_quant_finance_playbook.md)) e, para candidatos adaptativos, comparar com a **contraparte fixa**. Sem score sintético nem pesos na Fase 1.
5. **Relatório do experimento — blocos obrigatórios:**

```
Integrity checks:
- Look-ahead review: PASS / FAIL
- Point-in-time features: PASS / FAIL
- Replay assumptions unchanged: YES / NO
- New leakage risk introduced: YES / NO
- Leakage tests (05 §11) executed: YES / NO / N/A (motivo)

Overfitting review:
- Clear structural hypothesis: YES / NO
- Micro-parameter tuning (local numerical search) performed: YES / NO
- Added complexity justified: YES / NO
- Temporal stability checked: YES / NO
- PnL concentration acceptable: YES / NO
- Validation data consulted unnecessarily: YES / NO
- Baseline assumption challenged with a stated hypothesis (or N/A): YES / NO / N/A
- Excess over random-entry placebo reported: YES / NO
```
   - **Integridade:** o resultado só pode ser aceito com `PASS, PASS, YES, NO` (e testes executados ou N/A justificado). **Qualquer falha ⇒ o resultado não é aceito**: registrar como inválido, corrigir a causa e refazer; se a causa estiver no motor, seguir [05 §10](05_replay_trading_guide.md).
   - **Overfitting:** qualquer resposta desfavorável (sem hipótese estrutural, micro-ajuste feito, complexidade não justificada, estabilidade ou concentração não verificadas/inaceitáveis, validação consultada sem necessidade, placebo não reportado) ⇒ **REJECT ou, no máximo, REFINE cauteloso**; nunca KEEP até resolvido. **Métricas de destaque fortes não salvam um experimento cujo diagnóstico indica fragilidade.**
6. **Decidir e registrar:**
   - **KEEP:** hipótese sustentada; integridade e overfitting limpos; nenhuma dimensão degrada materialmente frente ao V0 sem justificativa; não é frágil ([06 §11](06_quant_finance_playbook.md)); a complexidade adicional merece seu lugar; amostra suficiente. Só candidatos KEEP são elegíveis a consulta à validação.
   - **REJECT:** hipótese falsificada, amostra insuficiente, risco de cauda/drawdown inaceitável, dependência de outliers, ou revisão de overfitting desfavorável.
   - **REFINE:** hipótese parcialmente sustentada e existe uma mudança **estrutural** (não numérica) específica a testar. Refinamentos por linhagem são limitados (máx. 2; proposta mantida em D2).
   - **INCONCLUSIVE:** a amostra ou o desenho não sustentam nem KEEP nem REJECT (ex.: < 30 trades, ou hipótese só parcialmente expressável); registrar o que faltaria para concluir. No livro de aprendizados vira INCONCLUSIVO, e pode ser refeito com melhor desenho.
7. **Placar top 3 (D3):** experimento KEEP que passa nos portões é comparado com os do placar segundo [06 §5](06_quant_finance_playbook.md); se for melhor, entra e o pior sai. Registrar a entrada/saída e o motivo (dimensão a dimensão) em `experiments/leaderboard.md`.
8. **Próximo experimento** deve testar uma hipótese materialmente diferente, salvo REFINE justificado.

Limiares numéricos dos portões: **aprovados em D3** ([06 §5](06_quant_finance_playbook.md): ≥ 30 trades; drawdown ≤ 15% do capital; top 5 trades ≤ 40% do lucro bruto; nenhum mês > 40% do lucro total; expectância > 0 após custos). São fixos: mudá-los exige o usuário e nunca é feito depois de ver resultados.

## 6. Orçamento de pesquisa e escalonamento

- **Orçamento por tempo (D2):** o usuário define **X minutos** de relógio em cada prompt-task; o agente registra o início e o prazo em `run.md`, **para no prazo** (um experimento em andamento é registrado como interrompido, não terminado às pressas), reporta quantos experimentos foram feitos e **não estende** sem o usuário. O agente **nunca** busca indefinidamente até achar estratégia lucrativa. Como o tempo não limita o nº de tentativas, **todo experimento conta como trial** e o total (acumulado entre runs) é reportado. "Otimização por X minutos" na Fase 1 significa **buscar arquiteturas dentro do prazo**, não ajustar limiares (Fase 2).
- Dentro do orçamento: testar hipóteses **materialmente diferentes**; não repetir microvariações da mesma ideia; **encerrar a família** de estratégias quando evidências repetidas rejeitarem a hipótese subjacente.
- **Consultas à validação** consomem orçamento e são registradas com motivo e candidato; somente para candidatos KEEP. **Nunca após cada experimento:** uso repetido é otimização indireta e faz da validação um dado de treino ([06 §6](06_quant_finance_playbook.md)).
- **Orçamento esgotado ou nenhuma família promissora:** parar e reportar "nenhum candidato suficientemente robusto" — resultado válido. Estender o orçamento é decisão do usuário.
- **Parar a pesquisa imediatamente** ao suspeitar de bug no motor ou de vazamento: seguir o procedimento de [05 §10](05_replay_trading_guide.md) e não comparar candidatos até haver decisão do usuário.
- **Parar e perguntar ao usuário antes de:** consultar validação além do previsto; abrir o holdout (nunca sem autorização); mudar o motor ou qualquer premissa de execução; ampliar o orçamento; iniciar a Fase 2.

## 7. Formato de handoff (colar ao fim de cada sessão)

```
## Handoff — <data> — <agente>
**Objetivo da sessão:** …
**O que foi feito (verificado):** …  (comandos rodados + resultado real)
**O que foi feito (não verificado):** …
**Arquivos alterados:** …
**Testes:** pytest -q → <resultado real>
**Experimentos (se Fase 1):** IDs, decisão de cada um, resultado dos blocos de integridade e overfitting, orçamento consumido / restante
**Decisões tomadas e por quê:** …
**Pendências / próximos passos:** …
**Riscos / dúvidas para o usuário:** …
```
Guardar em `docs/agentic_documentation/handoffs/AAAA-MM-DD_<agente>.md`.

## 8. Como reportar resultados ao usuário

- Começar pelo **fato mais importante**, sem jargão desnecessário.
- Incluir: conjunto de dados e período, `Config`, custos, nº de trades, aviso de amostra pequena, comparação com o V0 e **contagem de experimentos já realizados** (contexto de múltiplos testes).
- Diferenciar resultado **com e sem** custos.
- Apontar limitações e o que ainda pode invalidar a conclusão.
- Reportar candidatos rejeitados com a mesma clareza que os promissores.
- Não vender otimismo: um resultado positivo com IC largo é "inconclusivo".

## 9. Anti-padrões (não faça)

- Ajustar parâmetros até o gráfico ficar bonito; hill-climbing numérico na Fase 1 (mudanças **estruturais** de parâmetro com hipótese são permitidas).
- Trocar `intrabar_policy` para `target_first` "para ver"; alterar custos/slippage por candidato.
- Editar o motor para a estratégia render melhor.
- Consultar ou "só dar uma olhada" na validação/holdout; resumir a série completa em notebooks de pesquisa.
- Apagar, esconder ou reescrever experimentos ruins; relatar só os bons.
- Continuar experimentando até "dar certo".
- Re-testar uma hipótese já registrada em `experiments/knowledge.md` sem motivo de reabertura ("descer o nível") ou ignorar o livro de aprendizados.
- Racionalização pós-resultado: inventar a hipótese depois de ver o número.
- Empilhar regras porque cada uma melhora um pouco o backtest (estratégia "Frankenstein").
- Aceitar ou reportar como válido um experimento com qualquer check de integridade em FAIL.
- Usar `shift(-n)`, janelas centradas, `bfill`, agregados do dia corrente ou escalonadores ajustados na série inteira (tabela de [05 §5](05_replay_trading_guide.md)).
- Usar `fillna`/`dropna`/`ffill` sem contar quantas linhas afetou.
- Reordenar/reamostrar dados sem preservar timezone.
- Implementar regra do V0 "de memória" sem conferir o `.mq5`.
- Adicionar lógica de negócio apenas no notebook.
- Declarar "pronto" sem ter rodado os testes.

## 10. Comandos de referência

```powershell
conda activate wdo-backtest     # obrigatório; o .venv está obsoleto
pytest -q
jupyter notebook notebooks/01_wdo_opening_backtest.ipynb   # selecionar kernel "Python (wdo-backtest)"
```
Execução headless do notebook e recriação do ambiente: ver README desta pasta. Shell primário: PowerShell (sem `&&`; use `;` ou `if ($?) {}`). Git Bash também disponível.

## 11. Convenção de marcação em documentos

- **[verificado]**: confirmado executando ou lendo o trecho exato. **[não verificado]**: inferência.
- **R#**: risco registrado em [08](08_roadmap_and_open_questions.md). **Q#**: pergunta em aberto. **D#**: decisão metodológica pendente de aprovação.
