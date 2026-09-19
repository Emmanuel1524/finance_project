# EXP-0021 — ORB estrutural (EXP-0011) com ALVO ESTRUTURAL no extremo do dia anterior (PDH/PDL)
Pai: RUN-0002/EXP-0011. Ramo: Opening-Momentum. Família: arquitetura de saída (alvo estrutural).
**Checagem de novidade:** alvos FIXOS (6 e 20 pts) foram testados (EXP-0002/0003, NÃO SUSTENTADOS); alvo por ESTRUTURA nunca.
**hypothesis_source:** mecanismo (níveis de extremo do dia anterior concentram liquidez/ordens; realizar o lucro neles reduz a dependência de poucos trades grandes, a fragilidade do EXP-0011/0012). Independente da amostra.
**Premissa desafiada:** ausência de alvo (positive skew puro, top-5 ≈ 56–72% do lucro).
**Reabertura:** (i) mecanismo novo — alvo definido por estrutura, não por distância fixa.
**Hipótese:** com stop no extremo oposto da 1ª barra e alvo no extremo do dia anterior na direção do trade (PDH para compra, PDL para venda) quando esse nível estiver a pelo menos 2 pts da abertura (senão, sem alvo), a win rate sobe e a concentração cai sem destruir a expectância.
**Os 4 pontos (sem parâmetro numérico novo):** (i) sem alvo, poucos vencedores grandes dominam o lucro; (ii) `target_price` = PDH/PDL conhecido na abertura; (iii) muda a arquitetura de saída por estrutura, não é vizinho de alvo fixo; (iv) sustenta: expectância > 0 e acima do placebo com menor concentração; rejeita: caso contrário.
Graus de liberdade: 0 (a margem de 2 pts é guarda de validade do alvo). Nota: PDH/PDL vêm da série ajustada (R6).
