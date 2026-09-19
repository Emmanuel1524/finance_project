# Glossário

| Termo | Significado |
|---|---|
| **WDO** | Mini contrato futuro de dólar comercial da B3. Tick 0,5 pt; premissa R$ 10/pt/contrato (confirmar) |
| **WDOFUT** | Símbolo genérico do contrato vigente no MT5; a Genial faz crossorder para `WDO` |
| **B3** | Bolsa brasileira |
| **Genial** | Corretora (Genial Investimentos) usada no MT5 do EA |
| **MT5 / MQL5** | MetaTrader 5 / sua linguagem; `reference/mt5/Robo_Abertura_WDO_Genial_v1.35.mq5` é código MQL5 |
| **EA** | Expert Advisor: robô de trading do MT5 |
| **M5 / M1 / H1 / D1** | Candles de 5 min / 1 min / 1 hora / 1 dia |
| **OHLC(V)** | Open, High, Low, Close (e Volume) |
| **PDH / PDL** | Previous Day High / Low: máxima e mínima do dia anterior |
| **Canal superior/inferior** | `PDH − 7` e `PDL + 7` (offset configurável) |
| **EMA** | Média móvel exponencial (aqui 13/17/21 em H1 e D1) |
| **IFR / RSI** | Índice de Força Relativa (período 7, Wilder) |
| **Baseline V0** | Estratégia original (EA v1.35 replicado); comparador fixo de toda a pesquisa, nunca sobrescrita |
| **Candidate NNN** | Variante de estratégia com hipótese, pai, implementação e resultados rastreáveis |
| **Fase 1 / Fase 2** | Descoberta de arquitetura de estratégia / otimização de parâmetros (só depois) |
| **Conjunto de pesquisa / validação / holdout** | Partição temporal dos dados; holdout invisível até autorização (06 §6) |
| **Orçamento de pesquisa** | Nº máximo de experimentos significativos antes de parar (07 §6) |
| **Padrão 1–4** | Regras de entrada do EA (ver 02) |
| **Fade** | Operar contra o movimento (esperar reversão) |
| **Stop order** | Ordem que dispara quando o preço atinge um nível (rompimento) |
| **Limit order** | Ordem que executa a preço igual ou melhor |
| **Alvo / Stop (gain/loss)** | 6 pts / 10 pts |
| **Payoff ratio** | Ganho médio ÷ perda média |
| **Profit factor** | Lucro bruto ÷ perda bruta |
| **Drawdown** | Queda do pico da equity |
| **MAE / MFE** | Máxima excursão adversa / favorável por trade |
| **Slippage** | Diferença entre preço esperado e executado |
| **Look-ahead** | Uso de informação futura na decisão |
| **Point-in-time** | Só dados disponíveis naquele instante |
| **Walk-forward** | Otimizar em janela passada, testar na seguinte, rolando |
| **Holdout** | Amostra final reservada, usada uma única vez |
| **DSR / PBO** | Deflated Sharpe Ratio / Probability of Backtest Overfitting |
| **Rollover** | Troca do contrato vigente para o próximo vencimento |
| **Back-adjusted** | Série contínua com preços ajustados na emenda |
| **Intrabar** | O que acontece dentro de uma barra (sequência de high/low desconhecida em OHLC) |
| **`adverse`** | Política intrabar padrão: assume o pior caso para a estratégia |
| **Golden file** | Saída de referência versionada para testes de regressão |
| **Paper trading / shadow mode** | Operar sem dinheiro real / rodar sinais sem enviar ordens |
| **Kill switch** | Desligamento de emergência automático ou manual |
| **Crossorder** | Redirecionamento automático do símbolo genérico ao contrato vigente |
