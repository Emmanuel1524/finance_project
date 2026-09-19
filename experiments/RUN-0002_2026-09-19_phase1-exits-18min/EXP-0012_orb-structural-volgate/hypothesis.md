# EXP-0012 — ORB estrutural (EXP-0011) só em regime de volatilidade alta
Pai: EXP-0011. Ramo: Opening-Momentum. Família: momentum + arquitetura de saída + regime.
**hypothesis_source:** decomposição (DATA-INFORMED) reforçada por mecanismo: em dias de baixo range o movimento é pequeno frente a custo/slippage e à distância do stop; a continuação da 1ª barra precisa de range para se pagar. Literatura de regimes de volatilidade (fontes fracas) e Gao et al. 2018 (momentum mais forte em dias voláteis) apontam no mesmo sentido.
**Premissa desafiada:** operar todos os dias com a mesma arquitetura.
**Reabertura:** (i) mecanismo novo: o filtro de volatilidade (EXP-0001) só foi testado com saída fixa (NÃO SUSTENTADO); aqui atua sobre uma arquitetura de saída adaptada ao momentum.
**Hipótese:** restringir ao regime de alta volatilidade (D7, definição fixa) eleva a expectância e reduz drawdown sem novo parâmetro.
**Os 4 pontos:** (i) baixa vol perdeu em 4 arquiteturas; (ii) skip quando range do dia anterior <= mediana dos 20 pregões (D7); (iii) filtro de regime sobre arquitetura nova, não vizinho numérico; (iv) sustenta: expectância > 0 e acima do placebo, DD/concentração dentro dos portões com >= 30 trades; rejeita: caso contrário.
Graus de liberdade: 0 (D7 fixo). RISCO: a mesma amostra sugeriu e agora testa a regra (snooping): qualquer aprovação exige checkpoint de validação; n esperado ~45 (limítrofe).
