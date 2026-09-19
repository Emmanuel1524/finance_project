# EXP-0019 — ORB estrutural (EXP-0011) com UMA segunda entrada após stop (recuperação de rompimento falho)
Pai: RUN-0002/EXP-0011. Ramo: Opening-Momentum. Família: multi-trade.
**Checagem de novidade:** nunca testamos mais de 1 trade por dia (limite livre desde D9). Sem linha equivalente.
**hypothesis_source:** mecanismo (rompimentos falhos frequentemente reafirmam a direção depois de varrer stops: uma nova quebra fechada do mesmo extremo indica que a tese original volta a valer). Independente da amostra.
**Premissa desafiada:** limite de 1 trade por dia (V0).
**Reabertura:** — (família nova).
**Hipótese:** depois de o 1º trade ser stopado, permitir UMA re-entrada na mesma direção quando uma barra FECHADA fecha novamente além do extremo da 1ª barra (dentro da janela 09:00–10:30), com o mesmo stop estrutural e saída 17:55.
**Os 4 pontos:** (i) limite de 1/dia descarta a recuperação; (ii) `max_trades_per_day = 2` (Config do candidato) e regra de re-entrada acima; (iii) muda o limite diário (D9), não é um vizinho numérico; (iv) sustenta: expectância > 0 e acima do placebo sem piorar concentração e drawdown; rejeita: caso contrário.
Graus de liberdade: 0. Cuidado: trades no mesmo dia são correlacionados (não são 2 amostras independentes); DD pode subir.
