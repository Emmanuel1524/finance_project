# EXP-0015 — Fades do V0 (sem canal) com payoff simétrico 1:1 (stop 10 = alvo 10)
Pai: RUN-0001/EXP-0005 (fronteira; data-informed, usado como controle rotulado). Ramo: V0-Filters. Família: arquitetura de saída (payoff).
**hypothesis_source:** mecanismo (o payoff 0,6 do V0 obriga ~62,5% de acerto e perde ~R$12/trade sem edge; com 1:1 o ponto de equilíbrio cai para ~50% + custo) — Run 1, aprendizado estrutural 1. Sem fonte de literatura específica.
**Premissa desafiada:** o alvo curto de 6 pts (relação risco/retorno 0,6).
**Reabertura:** (i) mecanismo novo: EXP-0005/0006 só valem sob saída fixa 10/6; aqui muda-se a ESTRUTURA de payoff (1:1), não o alvo para vizinhos (6→6,5...).
**Os 4 pontos:** (i) alvo de 6 com stop de 10 exige acerto muito alto; (ii) alvo = stop = 10 pts (uma alternativa a priori, 0 novos parâmetros); (iii) muda o perfil de payoff de 0,6 para 1,0, não é um vizinho; (iv) sustenta: expectância > 0 e acima do placebo com portões OK; rejeita: caso contrário.
Graus de liberdade: 0. Nota: a entrada (V0 sem P3) é data-informed; sem contraparte adaptativa (controle já é o V0 de saída 10/6: EXP-0005).
