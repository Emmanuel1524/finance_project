# EXP-0020 — ORB de 5 min na ABERTURA DE NOVA YORK (09:30 ET), stop estrutural, saída 17:55
Pai: RUN-0002/EXP-0011 (mesma arquitetura, outro instante). Ramo: Opening-Momentum. Família: momentum na abertura dos EUA.
**Checagem de novidade:** o ORB só foi testado na abertura da B3 (09:00 BRT). Abertura de NY nunca testada.
**hypothesis_source:** literatura (sazonalidade intradiária da volatilidade em câmbio: pico na abertura de Londres/NY, Andersen & Bollerslev 1997; Ito & Hashimoto 2006) + mecanismo (o dólar/real reage à abertura dos EUA: dados e fluxo entram nesse instante). INDEPENDENTE da amostra.
**Premissa desafiada:** que a única janela relevante seja a abertura da B3 (09:00–10:30); janela livre (D9).
**Reabertura:** — (janela nova; arquitetura da fronteira).
**Hipótese:** o corpo da 1ª barra de 5 min a partir de 09:30 ET (10:30 BRT no horário de verão dos EUA, 11:30 BRT fora dele; o DST dos EUA começou em 2026-03-08 e a conversão é feita pelo fuso America/New_York) prediz a continuação; entrada na abertura da barra seguinte, stop no extremo oposto da barra, sem alvo, saída 17:55.
**Os 4 pontos (sem parâmetro alterado):** (i) a B3 abre sem os EUA; o fluxo dos EUA chega às 09:30 ET; (ii) mesma regra do EXP-0011 aplicada à barra das 09:30 ET; janela de sessão 09:00–12:00 BRT (Config do candidato) só para a estratégia enxergar as barras; (iii) outra janela do dia (construto: abertura dos EUA), não vizinho numérico; (iv) sustenta: expectância > 0 e acima do placebo com portões OK; rejeita: caso contrário.
Graus de liberdade: 0. Risco: tratamento de DST (feito por tz_convert, point-in-time); série ajustada (R6).
