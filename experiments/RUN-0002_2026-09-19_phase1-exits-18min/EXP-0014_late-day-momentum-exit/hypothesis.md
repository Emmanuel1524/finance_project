# EXP-0014 — Momentum intradiário de fim de dia (Gao et al. 2018) com saída por horário
Pai: RUN-0001/EXP-0008 (INVÁLIDO/BLOCKED, reaberto). Ramo: Intraday-Momentum-LateDay. Família: momentum intradiário.
**hypothesis_source:** literatura (Gao, Han, Li, Zhou, JFE 2018: retorno da 1ª meia hora, medido do fechamento anterior, prevê o da última meia hora; mais forte em dias voláteis).
**Premissa desafiada:** que só se opere a abertura (janela 09:00–10:30) e que toda saída seja stop/alvo fixo; janela livre (D9).
**Reabertura:** (i) MECANISMO NOVO: `ExitSpec.exit_time` (motor 1.1.0). O EXP-0008 era BLOCKED (sem saída por horário; posições atravessavam a noite): nada foi concluído.
**Hipótese:** r1 = fechamento das 09:30 / fechamento anterior - 1; entrar às 17:30 na direção de r1 e sair às 17:55 captura a continuação da última meia hora.
**Os 4 pontos:** (i) a saída fixa do EXP-0008 deixava o trade atravessar a noite; (ii) stop = 0,25 × range do dia anterior (única alternativa a priori) e saída por horário 17:55; janela de sessão 09:00–18:00 (Config do candidato); (iii) hipótese antes intestável, não um vizinho; (iv) sustenta: expectância > 0 e acima do placebo com portões OK; rejeita: caso contrário.
Graus de liberdade: 1 (K). Premissas: pregão regular até 18:00 (o dado tem barras até 18:25).
