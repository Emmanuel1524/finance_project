# CLAUDE.md — Projeto Quant WDO (finance_practice)

Diretrizes para trabalhar neste repositório. O objetivo de longo prazo é uma **estratégia produtizável, sólida e escalável**, e não apenas um backtest que "dá lucro". Na dúvida, prefira correção e reprodutibilidade a velocidade.

> **Documentação para agentes:** comece por `docs/agentic_documentation/README.md` (visão geral, especificação da estratégia, mapa do código, práticas de backtest/replay/quant, protocolo de handoff e riscos conhecidos). `AGENTS.md` traz as regras equivalentes para o Codex.

> **⚠️ Portão de pesquisa:** a Fase 1 (descoberta de estratégia) **não está autorizada**. Sem aprovação explícita do usuário: não rodar backtests de pesquisa, não alterar a estratégia, não otimizar parâmetros, não tocar validação/holdout. Metodologia completa: `docs/agentic_documentation/06`, `07` e `05 §10`; decisões pendentes D1–D7 em `08`.

## 1. Contexto do projeto

- Backtest em Python de um EA de abertura do WDO (Mini Dólar, B3), replicando o EA MQL5 v1.35 (`reference/mt5/Robo_Abertura_WDO_Genial_v1.35.mq5`; é a **fonte da verdade das regras do Baseline V0**, que é referência e não restrição para candidatos).
- Layout (detalhe no `README.md`): código em `src/wdo/` (pacote `wdo`), testes em `tests/`, notebooks só de pesquisa/relatório em `notebooks/`, cenários em `configs/*.toml`, dado bruto em `data/raw/`, saídas geradas em `outputs/` (fora do git), docs em `docs/`.
- Repositório git iniciado em 2026-09-19. O agente commita **apenas o registro de cada run, uma vez ao fim do prompt-task** (autorizado); qualquer outro commit só a pedido do usuário.
- **Ambiente obrigatório: conda `wdo-backtest`** (Python 3.12; ver `environment.yml`). Kernel do notebook: "Python (wdo-backtest)". O `.venv` (Python 3.14) está obsoleto. Detalhes e comando headless em `docs/agentic_documentation/README.md`.
- Windows/PowerShell é o shell principal.
- A pasta pai menciona Databricks, mas este projeto hoje é local. Não introduza dependências de Databricks sem pedido explícito.

## 2. Princípios inegociáveis (rigor quant)

1. **Zero look-ahead.** Qualquer feature, indicador, nível (PDH/PDL, EMAs H1/D1) só pode usar informação disponível **no instante da decisão**. Barra em formação nunca é usada como fechada. Todo indicador novo precisa de teste provando ausência de vazamento (mutação do futuro, histórico truncado, mutação da mesma barra: `docs/agentic_documentation/05` §11) e da revisão "este valor exato poderia ser conhecido neste timestamp em operação real?" (05 §5). Timing ambíguo ⇒ premissa conservadora.
2. **Zero survivorship / selection bias.** Não escolher período, parâmetros ou contratos olhando o resultado final.
3. **Premissa conservadora por padrão.** Com OHLC não se sabe a ordem dos extremos: manter `intrabar_policy="adverse"` como padrão. Nunca trocar o padrão para melhorar o resultado.
4. **Custos sempre explícitos.** Nenhum resultado financeiro é reportado sem custos, slippage e valor do ponto declarados. Resultado "sem custo" deve estar rotulado como tal.
5. **Fidelidade ao EA (só para o Baseline V0).** A implementação do V0 deve ter correspondência rastreável no MQL5 (comentário com padrão/função de origem); divergências são bugs ou decisões documentadas. Candidatos **não** precisam espelhar o EA: **o V0 é referência, não restrição** (ver `docs/agentic_documentation/06` §1–§2).
6. **Nunca inventar números.** Não reporte métricas que não foram executadas nesta sessão. Se testes falharam ou algo foi pulado, diga.
7. **Overfitting é o inimigo.** Duas fases separadas: Fase 1 (descoberta de arquitetura, sem ajuste fino de limiares) e Fase 2 (otimização, só depois). Toda tentativa é contada para correção de múltiplos testes; holdout invisível na Fase 1. Ver seção 6 e `docs/agentic_documentation/06`.

## 3. Dados

- Timezone canônico: `America/Sao_Paulo`, timestamps tz-aware. Nunca misturar naive e aware.
- Toda fonte passa por `validate_bars`: sem duplicatas, sem OHLC inválido (`low <= open,close <= high`), índice monotônico, sem buracos inesperados dentro do pregão.
- WDO é contrato por vencimento: usar `build_continuous_contract` com tabela de rollover explícita (`contract, start, end`). Sem sobreposição, sem lacunas. Documentar o critério de rollover (data fixa vs volume) e se há ajuste de preço (back-adjust) na emenda; gaps de rollover **não** podem gerar sinais falsos de PDH/PDL.
- Dados brutos são **imutáveis**: nunca editar `data/raw/wdo_data.csv` à mão. Transformações geram novos arquivos em `data/processed/` (Parquet), com hash/versão registrados.
- Estrutura alvo: `data/raw/`, `data/processed/`, `data/external/`. Arquivos grandes fora do git (DVC ou similar quando escalar).
- Calendário: considerar feriados B3, pregões encerrados cedo e mudanças de horário de verão históricas (o Brasil não tem mais DST, mas dados antigos podem ter).
- Toda carga de dado registra: fonte, intervalo, nº de linhas, hash. Reportar isso no notebook.

## 4. Motor de backtest

- Determinístico: mesma entrada + mesma `Config` = mesma saída, bit a bit. Sem `random` sem seed explícita.
- `Config` (dataclass) é a fonte dos parâmetros do cenário e da execução; cada candidato declara seus parâmetros de desenho em config própria, registrada no experimento (proveniência e graus de liberdade). Sem números mágicos espalhados. Preferir `@dataclass(frozen=True)` e validação no `__post_init__` (tick_size > 0, horários coerentes, etc.).
- Arredondar todo preço ao tick (`round_tick`, 0,5 pt no WDO) na entrada, saída, stop e alvo.
- Ordem de eventos dentro da barra é regra explícita e testada: pendentes → gatilhos → stop/alvo, conforme `intrabar_policy`. Se stop e alvo cabem na mesma barra, `adverse` assume o stop.
- 1 operação por dia é regra de estado (`day_state`), testada.
- Motor **separado** de I/O, plotagem e relatório. O motor recebe DataFrame + Config e devolve resultados; não lê arquivos nem imprime.
- Performance: não vetorizar às cegas o que precisa ser sequencial e dependente de estado. Vetorize features (pandas/numpy), mantenha a simulação de ordens em loop enxuto; se ficar gargalo, perfilar antes (cProfile/line_profiler) e só então considerar numba.
- Saídas mínimas: lista de trades, curva de equity (incluindo `in_position`), log de eventos (`ENTRY`, `EXIT`, cancelamentos) para auditoria.

## 5. Testes e validação

- `pytest -q` deve passar antes de qualquer conclusão de tarefa. Rode e reporte o resultado real.
- Cada regra da estratégia (Padrões 1–4, modos de canal 0/1/2, janela 09:00–10:30, cancelamento de pendentes) tem teste unitário com barras sintéticas e resultado esperado calculado à mão.
- Testes obrigatórios para qualquer mudança no motor:
  - **Look-ahead:** resultado em t independe de dados após t.
  - **Invariantes:** no máximo 1 posição, no máximo `max_trades_per_day` trades/dia (Config; 1 no V0), stop/alvo no lado certo, PnL = (saída − entrada) × lado × qtd × valor_ponto − custos.
  - **Regressão:** conjunto de trades de referência (golden file) versionado; mudança de resultado exige justificativa.
  - **Paridade com o MT5:** comparar trades do Python com o Strategy Tester do MT5 (mesmos dados/período) e documentar diferenças esperadas (ticks, bid/ask, EMAs em formação).
- Property-based testing (hypothesis) é bem-vindo para validação de dados e arredondamento.
- Um bug encontrado ganha um teste que o reproduz antes da correção.

## 6. Pesquisa e avaliação da estratégia

- Amostra: **pesquisa / validação / holdout final** por tempo (nunca aleatório); fronteiras exigem aprovação (D1). O holdout é invisível na Fase 1 e só é aberto uma vez, com autorização.
- **Aprendizado cumulativo:** antes de cada experimento consultar `experiments/knowledge.md` (checagem de novidade); não re-testar o que já foi testado sem motivo de reabertura; o pai padrão é a fronteira atual; atualizar o livro ao fim da run (docs 06 §10, 07 §5).
- **Baseline V0 é referência, não restrição:** regras, TP/SL, indicadores, limiares e sessão do V0 podem ser desafiados com hipótese; mudanças **estruturais** de parâmetro são Fase 1, hill-climbing numérico é Fase 2 (regra operacional em `docs/agentic_documentation/06` §2). Só a integridade da simulação é protegida (05 §10).
- Otimização (walk-forward, mapas de estabilidade de parâmetros) pertence à **Fase 2**; na Fase 1, hipóteses estruturais com racional de mercado, orçamento finito de experimentos e registro imutável (inclusive dos rejeitados).
- Múltiplos testes: registrar quantas configurações foram testadas; usar Deflated Sharpe Ratio / PBO ou ao menos Bonferroni/bootstrap antes de declarar edge.
- Significância: com poucas operações (estratégia de 1 trade/dia ≈ até ~170 trades em 8 meses), reportar **intervalos de confiança** (bootstrap por trade e por bloco), não só médias.
- Métricas mínimas: Net Profit, Profit Factor, Expected Payoff, Win Rate, Payoff, Max Drawdown (R$ e %), Recovery Factor, sequências de perdas, Sharpe/Sortino em retornos diários, exposição (% do tempo em posição), distribuição por hora/dia da semana/regime.
- Sensibilidade de execução obrigatória (ambas as fases): slippage (0/0,5/1/2 pts), custos, `intrabar_policy`. Sensibilidade paramétrica (offset do canal, tolerância de EMA etc.) é da Fase 2. Estratégia que só sobrevive com slippage zero não é robusta.
- Análise por regime: alta/baixa volatilidade, dias de gap, dias pós-evento (Copom, payroll, FOMC).
- Reportar **resultados negativos** com a mesma clareza que os positivos.

## 7. Estrutura do repositório

Estrutura atual (ver `README.md`); nova lógica vai para `src/wdo/`, **nunca** para o notebook:

```
finance_practice/
├── pyproject.toml            # pacote `wdo` (src layout) + config do pytest
├── environment.yml           # ambiente conda wdo-backtest
├── configs/                  # cenários em TOML (Config.from_toml)
├── src/wdo/
│   ├── config.py             # Config, round_tick
│   ├── data.py               # loaders, validação, rollover
│   ├── indicators.py         # RSI, EMAs (candles fechados, point-in-time)
│   ├── strategies/           # contrato Strategy + baseline_v0 (candidatos entram aqui)
│   ├── engine.py             # simulador congelado (ENGINE_VERSION), run_backtest
│   ├── partitions.py         # partições de dados e guarda (holdout inacessível)
│   ├── metrics.py            # métricas
│   └── reporting.py          # relatório e gráficos
├── tests/
├── notebooks/                # pesquisa/validação/relatório, sem lógica de negócio
├── data/{raw,processed}/     # raw imutável; processed gerado
├── reference/mt5/            # EA MQL5 (fonte da verdade do Baseline V0)
├── experiments/              # registro versionado: RUN-NNNN por prompt-task, EXP-NNNN, leaderboard top 3
├── docs/agentic_documentation/
└── outputs/                  # gerado (fora do git): notebooks executados, figuras, runs
```

Evolução prevista, só quando houver necessidade real: separar `strategy/` (regras puras, sem I/O) de `engine/` (execução, custos), adicionar `analytics/` (walk-forward, estatística) e `data/external/`.

- Refatorar **incrementalmente**, mantendo os testes verdes a cada passo. Não reescrever tudo de uma vez.
- Estratégia (decisão) separada de execução (fills, custos): permite reusar a mesma lógica em backtest, paper e produção.
- Interfaces estreitas e tipadas (`Protocol`/dataclasses). Estado mutável concentrado e explícito.

## 8. Qualidade de código

- Type hints em toda API pública; `mypy` (ou pyright) limpo no `src/`.
- `ruff` para lint + format. Sem código morto, sem comentários que narram o óbvio; comentar o **porquê** e a referência ao EA (função/padrão MQL5).
- Nomes de domínio consistentes com o EA (PDH, PDL, canal superior/inferior, padrão 1–4) para facilitar auditoria cruzada.
- Funções pequenas e puras sempre que possível; evitar o estilo denso de várias instruções por linha que existe hoje em partes de `src/wdo/` ao editar essas partes, prefira legibilidade.
- Sem `print` em biblioteca; usar `logging` com níveis. Relatórios só na camada `reporting`.
- Erros de dado **falham alto** (exceções claras). Nunca engolir exceção ou preencher silenciosamente (`fillna`, `dropna`) sem registrar quantas linhas foram afetadas.
- Dinheiro/preço: cuidado com float. Comparações de preço via tick inteiro (preço / tick_size) ou tolerância explícita.

## 9. Reprodutibilidade e experimentos

- Dependências com versão fixada (lockfile: `uv.lock`/`pip-tools`). `environment.yml`/`pyproject.toml` usam `>=`; ao produtizar, pinar.
- Cada execução relevante grava: hash do dado, `Config` completa, versão do código (commit), seed, data/hora, métricas. Rastreamento via MLflow ou, no mínimo, um JSON/Parquet em `runs/<timestamp>/`. Para experimentos de pesquisa, o registro imutável e seus campos obrigatórios estão em `docs/agentic_documentation/07` §4 (local: decisão D4).
- Notebooks: executar de ponta a ponta antes de considerar concluído (`Restart & Run All`); limpar outputs volumosos; nenhuma lógica exclusiva de notebook (importar de `src/`).
- Resultados numa tabela de experimentos (o que foi testado, hipótese, resultado), evitando repetir testes e p-hacking involuntário.

## 10. Caminho para produção

Quando a estratégia passar na validação (seção 6), o pipeline segue estas etapas, cada uma com critério de saída claro:

1. **Paridade backtest × MT5** documentada.
2. **Paper trading / forward test** em conta demo por período pré-definido, comparando fills reais × simulados (slippage real, rejeições, latência).
3. **Go-live reduzido** (1 contrato), com limites duros.
4. **Escala gradual** só com evidência de que o slippage e a capacidade suportam.

Requisitos de produção:
- **Risco:** stop diário de perda, limite de posição, kill switch, checagem de horário e de dados atrasados/faltantes antes de operar.
- **Execução idempotente**: nunca enviar ordem duplicada em retry; reconciliar posição/ordens com a corretora ao iniciar.
- **Observabilidade:** logs estruturados, métricas (PnL, slippage, rejeições), alertas (falha de feed, divergência de posição, drawdown acima do limite).
- **Monitoramento de decaimento:** comparar performance live × backtest continuamente; critério objetivo para desligar a estratégia.
- **Segredos** (credenciais de corretora/API) só em variáveis de ambiente ou cofre, jamais em código, notebook ou git.
- **Config por ambiente** (backtest/paper/live) com a mesma lógica de estratégia.
- CI: lint + tipos + pytest a cada mudança. Deploy de estratégia só com testes verdes e revisão.

## 11. Escalabilidade

- Pensar em múltiplos ativos/estratégias desde já: nada de "WDO" hardcoded fora de `Config` (tick size, valor do ponto, horário, calendário por instrumento).
- Formato de dados colunar (Parquet) e particionado por instrumento/data quando o volume crescer; dados de ticks/book exigem outra estratégia de armazenamento.
- Backtests independentes por período/parâmetro são embaraçosamente paralelos (`concurrent.futures`/joblib); manter o motor sem estado global para permitir isso.
- Se migrar para Databricks/Spark no futuro, manter a lógica da estratégia como funções puras em Python reutilizáveis, e usar a plataforma apenas para orquestração, armazenamento e paralelização de varreduras.

## 12. Como o Claude deve trabalhar aqui

- **Ler antes de editar**: consultar `reference/mt5/Robo_Abertura_WDO_Genial_v1.35.mq5` ao mexer em regras **do V0**; confirmar o comportamento no EA, não presumir.
- Ao alterar regra de negócio: atualizar o teste correspondente, rodar `pytest -q`, e informar o resultado real.
- Ao apresentar resultados de backtest: sempre incluir período, `Config`, custos/slippage, nº de trades e advertência de amostra pequena quando aplicável.
- Mudanças que alteram resultados históricos (motor, dados, config padrão) exigem destaque explícito no resumo e comparação antes/depois.
- Nunca editar o motor de replay para melhorar o desempenho de uma estratégia; preservar o Baseline V0; não apagar experimentos ruins.
- Não instalar dependências novas, não alterar dados brutos, não mudar defaults conservadores e não commitar fora do autorizado (registro ao fim de cada run) **sem pedir**.
- Comunicação em **português (pt-BR)**; código, nomes de símbolos e mensagens de commit podem seguir o padrão já existente (código em inglês, termos de domínio em português quando espelham o EA).
- Ser explícito sobre incerteza: distinguir "verificado rodando" de "inferido lendo o código".
- Preferir mudanças pequenas e revisáveis a grandes reescritas; propor o plano antes de refatorações estruturais.

## 13. Comandos úteis

```powershell
# ativar ambiente (obrigatório; NÃO usar .venv)
conda activate wdo-backtest

# criar o ambiente, se ainda não existir
conda env create -f environment.yml

# testes
pytest -q

# notebook
jupyter notebook notebooks/01_wdo_opening_backtest.ipynb
```

## 14. Checklist antes de dar uma tarefa por concluída

- [ ] `pytest -q` executado e resultado reportado
- [ ] Sem look-ahead introduzido (teste incluído se houver feature nova)
- [ ] Regra do V0 confere com `reference/mt5/Robo_Abertura_WDO_Genial_v1.35.mq5` (candidatos: hipótese e premissa desafiada registradas)
- [ ] Custos/slippage/valor do ponto explícitos nos resultados
- [ ] Nenhum parâmetro mágico fora de `Config`
- [ ] Mudança de resultado histórico destacada e justificada
- [ ] Notebook (se tocado) executa de ponta a ponta
