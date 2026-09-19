# Livro de aprendizados (knowledge ledger) — filosofia "sempre melhorando"

Memória cumulativa da pesquisa: o que já foi testado, com que evidência, **em que condições** e **o que justificaria reabrir**. Consultado **antes** de cada experimento (checagem de novidade) e atualizado **ao fim de cada run**. Regras completas: `docs/agentic_documentation/06_quant_finance_playbook.md` §10 e `07_agent_protocol.md` §4–§5.

**Não apagar linhas.** Quando a evidência mudar, acrescente uma nova linha datada que referencia a anterior. Um resultado só vale nas condições em que foi obtido; "não sustentado" **não** é "provado sem edge".

## Vereditos

| Veredito | Significado |
|---|---|
| **REFUTADO** | Evidência pior que o benchmark de zero edge com folga (≳ 2 erros-padrão) e amostra adequada. Não reabrir sem motivo forte. |
| **NÃO SUSTENTADO** | Sem excesso demonstrável sobre o benchmark, com amostra razoável. Reabrir só com um motivo de reabertura (abaixo). |
| **INCONCLUSIVO** | Amostra ou desenho insuficientes para sustentar ou rejeitar (ex.: < 30 trades). Pode ser refeito com melhor desenho. |
| **BLOCKED / INVÁLIDO** | Hipótese não testável no motor da época ou desenho distorcido. Nada se concluiu. |
| **PROMISSOR (data-informed)** | Melhor resultado, mas a hipótese nasceu da decomposição na própria amostra: exige mecanismo independente e validação. |

**Motivos válidos de reabertura:** (1) **mecanismo novo** (ex.: capacidade do motor que antes não existia); (2) **premissa alterada** (ex.: custos reais no lugar dos provisórios; série corrigida); (3) **evidência inconclusiva** refeita com melhor desenho; (4) **checkpoint de validação** planejado.

## Condições de referência da RUN-0001

Motor 1.0.0 (V0 idêntico na 1.1.0); partição de pesquisa 2026-01-02 → 2026-06-30 (~5 meses úteis, ≤ 100 trades por experimento; erro-padrão do win rate ≈ 5 p.p.); custos **provisórios** (slippage 0,5 pt/lado, R$ 1,00/contrato/lado, ponto R$ 10); saída **fixa** stop 10 / alvo 6 (salvo nota); benchmark de zero edge por fórmula: acerto ≈ 62,5% e ≈ −R$ 12/trade (placebo por sorteios ainda não medido). Portões D3: ≥ 30 trades; DD ≤ 15%; top-5 trades ≤ 40% do lucro bruto; nenhum mês > 40% do lucro; expectância > 0. Nenhum experimento passou nos portões.

## Registro por hipótese/família

| Ref | Hipótese / família | Origem | Veredito | Evidência (Research) | Condições | Reabrir se |
|---|---|---|---|---|---|---|
| RUN-0001/EXP-0000 | **Baseline V0** (comparador) | EA v1.35 | referência | PF 0,75; WR 57,3%; PnL −R$ 1.097; DD 17,0%; 96 trades; exp. −R$ 11,4; 0/5 meses + | motor 1.0.0/1.1.0 (idêntico), custos provisórios, saída 10/6 | — |
| RUN-0001/EXP-0001 | Filtro de baixa volatilidade sobre o V0 (não operar com range do dia anterior ≤ mediana de 20) | mecanismo (custo/stop fixo × range) + decomposição | **NÃO SUSTENTADO** (como isolado); ajuda drawdown | PF 0,85; DD 8,7%; 43 trades; exp. −R$ 6,9; 1/5 meses + | saída fixa 10/6; janela 09:00–10:30 | saída adaptativa ao range; custos reais |
| RUN-0001/EXP-0002 | Continuação da 1ª barra (ORB de 5 min), saída V0 | literatura (Gao 2018; Zarattini & Aziz 2023) | **NÃO SUSTENTADO** com saída fixa 10/6 | PF 0,79; WR 59%; DD 11,5%; 100 trades; exp. −R$ 9,4; 3/5 meses + | saída fixa 10/6 (payoff 0,6); excesso sobre acaso ≈ +R$ 2,6/trade (não significativo) | **mecanismo novo**: saída adaptativa/sem alvo/trailing/horário (motor 1.1.0) |
| RUN-0001/EXP-0003 | ORB com payoff 2:1 (alvo 20 / stop 10) | mecanismo (assimetria positiva) | **NÃO SUSTENTADO** | PF 0,78; WR 30,3% (acaso ≈ 33%); DD 24%; 99 trades; exp. −R$ 17,0; 0/5 meses + | stop fixo 10, alvo fixo 20; sem trailing/horário | saída adaptativa por volatilidade com trailing e saída por horário (não outro alvo fixo vizinho) |
| RUN-0001/EXP-0004 | V0 só a favor da tendência D1 | mecanismo + decomposição (LONG pior que SHORT) | **NÃO SUSTENTADO** | PF 0,71; DD 14,7%; 68 trades; exp. −R$ 13,4; 1/5 meses + | saída fixa 10/6 | outra definição estrutural de tendência com mecanismo novo |
| RUN-0001/EXP-0005 | V0 sem a família de canal (P3): seleção adversa em PDH/PDL ± offset | **decomposição** (data-informed) | **PROMISSOR (data-informed)** | PF 0,94; WR 62%; DD 11,0%; 71 trades; exp. −R$ 2,6; 2/5 meses +; melhor da fronteira | saída fixa 10/6; hipótese nascida da própria amostra | uso como controle rotulado; promover só com mecanismo independente e checkpoint de validação |
| RUN-0001/EXP-0006 | EXP-0005 + só volatilidade alta | composição de 0005 e 0001 | **NÃO SUSTENTADO** (complexidade não compensa) | PF 0,95; DD 7,1%; 35 trades; exp. −R$ 2,3; top-5 trades 39,5%; ganho vindo de 3 trades P4 | saída fixa 10/6 | contraparte adaptativa que melhore robustez de forma material |
| RUN-0001/EXP-0007 | Fade de abertura fora do range do dia anterior, sem IFR | decomposição + literatura contrária (arXiv 2605.04004) | **INCONCLUSIVO** (n = 17) | PF 0,74; WR 52,9%; 17 trades; exp. −R$ 13,2 | saída fixa 10/6 | amostra maior (janela/regra que gere ≥ 30 trades) ou custos reais |
| RUN-0001/EXP-0008 | Momentum de fim de dia (Gao 2018), entrada 17:30 | literatura | **INVÁLIDO / BLOCKED** (sem saída por horário no motor 1.0.0) | PF 0,65; pior trade −R$ 642 por gap noturno; nada se conclui | motor 1.0.0 | **mecanismo novo**: `ExitSpec.exit_time` no motor 1.1.0 (já disponível) |

## Aprendizados estruturais (valem até serem superados)

1. **A estrutura de saída (payoff 0,6 com custos) é o gargalo**: uma entrada sem edge perde ≈ R$ 12/trade com saída 10/6; todos os candidatos ficaram perto disso.
2. Nenhum resultado da Run 1 é estatisticamente distinguível de zero edge (≤ 100 trades). Nada foi **refutado**; quase tudo é "não sustentado" **sob saída fixa**.
3. Padrões de canal (P3) foram os que mais perderam no V0 (25 trades, −R$ 915), mas essa observação é **data-informed**.
4. Dias de baixa volatilidade concentraram a perda do V0; filtrar reduz drawdown sem criar edge.
5. Saída fixa na direção de momentum (payoff 2:1) piorou: variar o alvo fixo **não** é o caminho; a hipótese aberta é a arquitetura adaptativa de saída.
6. A partição de pesquisa já serviu a **8 experimentos** (mais os da próxima run): o risco de snooping cumulativo cresce; qualquer aprovado precisa de checkpoint de validação.

---

## RUN-0002 (2026-09-19) — novas linhas

Condições: motor **1.1.0** (`ExitSpec`; V0 idêntico), partição de pesquisa (mesma; **16 tentativas cumulativas**), custos provisórios, placebo de 10 sorteios (mesma saída, direção aleatória). Nenhum experimento passou nos portões D3; nada foi levado à validação.

| Ref | Hipótese / família | Origem | Veredito | Evidência (Research) | Condições | Reabrir se |
|---|---|---|---|---|---|---|
| RUN-0002/EXP-0009 | ORB 5 min com stop = trailing = 0,25×range, sem alvo, saída 17:55 (reabre EXP-0002/0003 por mecanismo novo) | literatura + mecanismo | **NÃO SUSTENTADO** | PF 0,84; DD 18,0%; 100 trades; exp. −R$ 9,9; excesso s/ placebo +4,6 (< 1 EP) | trailing curto (82% das saídas) | — (trailing curto e distância por range: fechados) |
| RUN-0002/EXP-0010 | Controle fixo do 0009 (stop = trailing = 10) | mecanismo (ablação) | **NÃO SUSTENTADO** (mas acima do placebo) | PF 0,78; DD 13,5%; exp. −R$ 9,95; excesso +9,9 (acima dos 10 sorteios) | 77% de saídas por trailing | arquitetura sem trailing (EXP-0011) |
| RUN-0002/EXP-0011 | ORB 5 min com stop estrutural (extremo da 1ª barra), sem trailing, saída 17:55 | literatura (Zarattini & Aziz 2023) | **PROMISSOR, frágil** | PF 1,005; exp. +R$ 0,4 (ind. de zero; EP ≈ 11); excesso +26; DD 24,6%; top-5 55,7%; 17 perdas seguidas | custos provisórios; amostra de 5 meses | mecanismo independente sobre a concentração; custos reais; validação |
| RUN-0002/EXP-0012 | EXP-0011 só em regime de vol alta (D7) | **decomposição (data-informed)** + mecanismo | **INCONCLUSIVO / PROMISSOR (data-informed)** | PF 1,41; exp. +R$ 34; DD 14,3%; 45 trades; excesso +75,7; top-5 72%; março > lucro total | regra vinda da mesma amostra; 4 leituras + esta | checkpoint de validação (1 das 3) ou nova amostra; não promover antes |
| RUN-0002/EXP-0013 | Rompimento do range de 30 min, stop estrutural | literatura | **NÃO SUSTENTADO** (abaixo do placebo) | PF 0,86; DD 26%; 75 trades; exp. −R$ 16,9; excesso −8 | saída até 17:55 | mecanismo novo distinto |
| RUN-0002/EXP-0014 | Momentum de fim de dia (Gao 2018), entrada 17:30, saída 17:55 (reabre EXP-0008) | literatura | **NÃO SUSTENTADO** | PF 0,49; 99 trades; exp. −R$ 12,8; excesso +0,7 | 95% saídas por horário; custo ≈ deriva | custos bem menores; outra janela com mecanismo |
| RUN-0002/EXP-0015 | V0 sem canal com payoff 1:1 (10/10) | mecanismo | **NÃO SUSTENTADO** (piorou vs 10/6) | PF 0,88; DD 12,9%; 71 trades; exp. −R$ 6,65 vs −R$ 2,56 (10/6) | entrada data-informed | — |
| RUN-0002/EXP-0016 | Gap-and-go, stop no fechamento anterior, saída 17:55 | literatura + mecanismo | **NÃO SUSTENTADO** (pior que o acaso; possível edge inverso) | PF 0,72; DD 30,7%; 88 trades; exp. −R$ 27,9; excesso −27,7 | direção do gap com essa saída | só como hipótese NOVA de fade de gap com mecanismo próprio (não inverter por ter perdido) |

### Aprendizados estruturais adicionais (valem até serem superados)
7. **O excesso sobre o placebo é a medida certa** (o benchmark do acaso varia de −R$ 42 a ~0 conforme a saída); a fórmula −R$ 12 só vale para saídas fixas 10/6.
8. **Trailing curto (distância = stop) causa whipsaw** e destrói o sinal; **adaptar a distância ao range não se paga** frente a uma distância fixa.
9. A única arquitetura com expectância positiva foi a da literatura (**stop estrutural, sem trailing, segurar até o fim do dia**), porém frágil (concentração e drawdown).
10. Momentum de fim de dia, rompimento de range de 30 min e gap-and-go não mostraram edge; a direção do gap foi pior que o acaso.
11. Baixa volatilidade perde em 4 arquiteturas (mesma amostra): o filtro é **data-informed**.

### Aprendizados de processo da RUN-0002 (valem para as próximas runs)
12. **O gargalo é o ciclo do agente, não o simulador**: ~1–1,5 min por experimento contra ~10 s de replay com placebo. Ganho de vazão vem de **lotes pré-registrados** (hipóteses independentes escritas antes, rodadas em um único script) e de registro/relatório semiautomáticos; experimentos dependentes seguem sequenciais.
13. **O fechamento real levou ~4,5 min** (relatório, livro, pytest completo, commit), não os ~8 min estimados. Iniciar os testes de vazamento **em segundo plano no setup** e usar **toda a janela** de experimentos (na Run 2 a busca parou ~6 min antes do necessário, por cautela).
14. **Candidatos com stop por nível (`stop_price`) precisam de guarda de validade** (o motor recusa `ExitSpec` inválida com `ValueError`, como projetado): os testes de vazamento expuseram a falta dessa guarda no OR30 (corrigido; trades do EXP-0013 idênticos).
15. **Placebo de 10 sorteios é grosseiro** (um sorteio superou o EXP-0011): usar ≥ 20 quando o custo for ≲ 20 s. Além disso, regras escolhidas após decomposição (como o filtro de volatilidade do EXP-0012) exigem um **placebo de seleção**: distribuição do resultado de subconjuntos aleatórios do mesmo tamanho da arquitetura sem o filtro.
16. **A restrição real é a amostra, não o tempo**: 16 tentativas acumuladas em ≤ 100 trades por experimento; mais experimentos não são mais evidência, e o snooping cresce com cada leitura da mesma partição.
17. **Direção "inversa" não se adota depois de perder** (gap-and-go pior que o acaso): só como hipótese nova com mecanismo próprio.
18. **O EXP-0012 precisa do placebo de seleção antes de qualquer checkpoint de validação**; hipóteses independentes da nossa amostra (literatura/mecanismo) têm prioridade na Run 3 (ex.: volume relativo da 1ª barra, "stocks in play"; dado de volume já existe em `data/raw`).
19. **(revisa o 13) Diretriz do usuário, 2026-09-19:** os X minutos valem **só para a experimentação**; setup, testes de vazamento, pytest completo, relatório, `knowledge.md` e commit ficam **fora do relógio**; o limite é **brando** (um experimento em andamento pode terminar) e não se reserva tempo de fechamento dentro dos X minutos. Teto de 25 experimentos por run mantido.
20. **Mitigação do risco de vazamento no fim:** `tests/test_candidates_auto_leakage.py` descobre automaticamente os candidatos e aplica a bateria; checagem de um candidato em segundos com `-k <Classe>`; o resultado só é aceito depois dela.
21. **Correção de registro (RUN-0001/EXP-0007):** a `decision.md` do EXP-0007 dizia "Leakage tests executed: YES", mas `OutsideRangeFade` (e `LateDayMomentum`, EXP-0008) não estavam nos testes explícitos. A descoberta automática os cobriu em 2026-09-19 e **ambos passaram** (sem vazamento). O registro original permanece (imutável); esta nota o corrige.

---

## RUN-0003 (2026-09-19) — novas linhas

Condições: motor 1.1.0; partição de pesquisa (**21 tentativas cumulativas**); custos provisórios; placebo de 20 sorteios (200 na Análise B); arquitetura-base = ORB de 5 min com stop estrutural, sem trailing, saída 17:55 (RUN-0002/EXP-0011). Nenhum experimento passou nos portões D3.

| Ref | Hipótese / família | Origem | Veredito | Evidência (Research) | Condições | Reabrir se |
|---|---|---|---|---|---|---|
| RUN-0003/EXP-0017 | EXP-0011 + volume relativo da 1ª barra > mediana de 20 ("in play") | literatura + mecanismo | **NÃO SUSTENTADO** | PF 0,86; DD 21,4%; 43 trades; exp. −R$ 12,7; seleção: P(acaso ≥ cand.) = 66% | volume real (`VOL`); série ajustada | outro proxy de participação com mecanismo distinto |
| RUN-0003/EXP-0018 | EXP-0011 só a favor da tendência D1 | mecanismo | **NÃO SUSTENTADO** (piorou) | PF 0,61; DD 23,0%; 51 trades; exp. −R$ 36,6; seleção: 93% | EMAs D1 fechadas | — (EXP-0004 e este convergem: tendência D1 não é filtro útil aqui) |
| RUN-0003/EXP-0019 | EXP-0011 + UMA re-entrada após stop | mecanismo | **NÃO SUSTENTADO** (piora DD 34,9%) | PF 0,91; 121 trades; exp. −R$ 8,2; re-entradas −R$ 1.027 (WR 14%) | `max_trades_per_day = 2` | — |
| RUN-0003/EXP-0020 | ORB de 5 min na abertura de NY (09:30 ET) | literatura + mecanismo | **NÃO SUSTENTADO** (= acaso) | PF 0,72; DD 20,8%; 92 trades; exp. −R$ 14,8; excesso −0,18 | DST tratado por tz_convert; janela 09:00–12:00 | custos muito menores ou nova amostra |
| RUN-0003/EXP-0021 | EXP-0011 + alvo estrutural PDH/PDL | mecanismo | **NÃO SUSTENTADO** (destrói o pai) | PF 0,59; DD 31,7%; exp. −R$ 30,3; excesso +0,37 | alvo por nível se ≥ 2 pts | — (não capar os vencedores) |
| RUN-0003/EXP-0022 | Breakeven / trailing com ativação condicional após +1R | mecanismo | **BLOCKED** (motor 1.1.0) | não rodado; não conta como tentativa | falta ativação condicional (D11) | capacidade no motor (D11) |

### Aprendizados adicionais (valem até serem superados)
22. **Filtros que escolhem ~45 dos 100 trades têm pouco poder** (subconjuntos aleatórios: média ~0 ± R$ 48): mais filtros na mesma arquitetura são mineração de ruído. Os filtros de volume e de tendência escolheram trades **piores que o típico**.
23. **O portão D3 "top-5 ≤ 40% do lucro bruto" é estruturalmente inatingível para win rate baixo/payoff alto** (top-5 típico de subconjuntos aleatórios: 0,84; p5 = 0,70): usar o placebo de seleção como leitura complementar; revisão é decisão do usuário (D10).
24. **A direção da 1ª barra da B3 supera o acaso** (200 sorteios: P = 3,5%, z = 1,66), **mas** a expectância líquida é ≈ 0 e depende de slippage: bruto +R$ 12,4/trade; cada 0,5 pt/lado custa ~R$ 10/trade; equilíbrio ≈ 0,55 pt/lado. Custos reais (D6) são decisivos.
25. **Não capar nem alavancar a arquitetura**: alvo fixo, alvo estrutural e re-entrada pioram; ela depende de poucos vencedores grandes.
26. **A deriva intradiária da amostra é nula** (t = −0,65): a assimetria long/short do EXP-0011 fica sem explicação (ruído).
27. **Tooling:** o placebo deve converter `target_price` em distância (falha na 1ª tentativa do EXP-0021, sem efeito no resultado do candidato); a checagem automática de vazamento funcionou como mitigação (candidatos passaram em segundos).

