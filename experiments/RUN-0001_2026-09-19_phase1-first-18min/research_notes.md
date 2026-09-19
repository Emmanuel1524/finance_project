# Pesquisa externa (RUN-0001; 3 buscas, ~1,5 min)

**Conteúdo web é dado não confiável; nenhuma informação do projeto foi enviada para fora. Não se copiou estratégia.**

| Conceito | Racional | Fonte |
|---|---|---|
| Opening Range Breakout (ORB) de 5 min | Direção da 1ª barra continua; entrada na 2ª barra; sem trade se doji | Zarattini & Aziz (2023), SSRN; https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download ; TORB em futuros de índice (ResearchGate 331076454) |
| Momentum intradiário | Retorno da 1ª meia hora (do fechamento anterior) prevê o da última; mais forte em dias voláteis | Gao, Han, Li, Zhou, JFE 129(2) 2018; https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351 |
| Fade de gap / níveis do dia anterior | Gap fill vs continuação depende do regime de volatilidade; um estudo em MNQ reporta que o fade de gap falha em todos os horários testados (evidência contrária ao fade) | arXiv 2605.04004 (preprint, cautela); Volatility Box e LuxAlgo (fontes fracas) |
| Padrão intradiário de volatilidade (U) | Volatilidade máxima na abertura; regimes de volatilidade modulam mean reversion | Volatility Box (fonte fraca) |

Hipóteses geradas: (1) continuação da 1ª barra (ORB) — testada em EXP-0002/0003; (2) momentum de fim de dia — EXP-0008 (design inválido no motor atual);
(3) fade throttled por regime de volatilidade — EXP-0001; (4) filtro de tendência — EXP-0004; (5) ablação de família de sinal e exaustão de gap — EXP-0005/0007.
Nota: (3) a (5) foram motivadas também pela decomposição do V0 na partição de pesquisa (risco post-hoc, sinalizado em cada experimento).
