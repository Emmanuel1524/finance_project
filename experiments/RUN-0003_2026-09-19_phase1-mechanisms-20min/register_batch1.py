import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools

H17 = """# EXP-0017 — ORB estrutural (EXP-0011) só com volume relativo alto da 1ª barra ("in play")
Pai: RUN-0002/EXP-0011 (arquitetura da fronteira). Ramo: Opening-Momentum. Família: momentum + filtro de participação.
**Checagem de novidade (knowledge.md):** volume nunca foi usado; sem linha equivalente.
**hypothesis_source:** literatura (Zarattini, Barbon & Aziz 2024, "stocks in play": ORB funciona melhor quando o volume relativo de abertura é alto) + mecanismo (participação informada favorece a continuação da 1ª barra). INDEPENDENTE da nossa amostra.
**Premissa desafiada:** operar todos os dias com o mesmo critério de qualidade do sinal.
**Reabertura:** (i) mecanismo novo — filtro independente do regime de volatilidade (o EXP-0012 usa range do dia anterior; este usa volume da 1ª barra).
**Hipótese:** o sinal de continuação é mais confiável quando o volume da 1ª barra excede a mediana dos volumes das 1ªs barras das 20 sessões anteriores; sem 10 sessões de histórico não opera.
**Os 4 pontos:** (i) o sinal de 1 barra é ruidoso e a participação varia por dia; (ii) filtrar por volume relativo da 1ª barra (mediana de 20 sessões passadas, mesma janela do D7, sem novo limiar), mesma saída do EXP-0011; (iii) filtro por outra variável (volume), não vizinho numérico; (iv) sustenta: expectância > 0 e acima do placebo, com placebo de seleção favorável e portões avaliados; rejeita: caso contrário.
Graus de liberdade: 0 (janela 20 e histórico mínimo 10 reutilizam D7). Ressalva: colunas de volume do arquivo MT5 (`VOL`, volume real), série ajustada (R6).
"""

H18 = """# EXP-0018 — ORB estrutural (EXP-0011) só a favor da tendência D1
Pai: RUN-0002/EXP-0011. Ramo: Opening-Momentum. Família: momentum + alinhamento de tendência.
**Checagem de novidade:** EXP-0004 (alinhamento de tendência) testou só FADES do V0 com saída fixa (NÃO SUSTENTADO). Aqui é continuação (momentum) com saída estrutural.
**hypothesis_source:** mecanismo (a continuação de um impulso de abertura é mais provável a favor da tendência dominante; contra ela, o impulso tende a ser absorvido). Independente da amostra.
**Premissa desafiada:** operar os dois lados independentemente da tendência diária.
**Reabertura:** (i) mecanismo novo — a lógica é o oposto do fade: alinhar continuação, não reversão, e com arquitetura de saída diferente.
**Hipótese:** com a abertura acima das 3 EMAs D1 fechadas só se compra; abaixo das 3, só se vende; entre elas, sem filtro (mesma regra do EXP-0004).
**Os 4 pontos:** (i) impulsos contra a tendência sofrem mais reversão; (ii) descartar entradas contra a tendência D1, mesma saída do EXP-0011; (iii) filtro direcional, não vizinho numérico; (iv) sustenta: expectância > 0 e acima do placebo com placebo de seleção favorável; rejeita: caso contrário.
Graus de liberdade: 0 (EMAs 13/17/21 do motor).
"""

H19 = """# EXP-0019 — ORB estrutural (EXP-0011) com UMA segunda entrada após stop (recuperação de rompimento falho)
Pai: RUN-0002/EXP-0011. Ramo: Opening-Momentum. Família: multi-trade.
**Checagem de novidade:** nunca testamos mais de 1 trade por dia (limite livre desde D9). Sem linha equivalente.
**hypothesis_source:** mecanismo (rompimentos falhos frequentemente reafirmam a direção depois de varrer stops: uma nova quebra fechada do mesmo extremo indica que a tese original volta a valer). Independente da amostra.
**Premissa desafiada:** limite de 1 trade por dia (V0).
**Reabertura:** — (família nova).
**Hipótese:** depois de o 1º trade ser stopado, permitir UMA re-entrada na mesma direção quando uma barra FECHADA fecha novamente além do extremo da 1ª barra (dentro da janela 09:00–10:30), com o mesmo stop estrutural e saída 17:55.
**Os 4 pontos:** (i) limite de 1/dia descarta a recuperação; (ii) `max_trades_per_day = 2` (Config do candidato) e regra de re-entrada acima; (iii) muda o limite diário (D9), não é um vizinho numérico; (iv) sustenta: expectância > 0 e acima do placebo sem piorar concentração e drawdown; rejeita: caso contrário.
Graus de liberdade: 0. Cuidado: trades no mesmo dia são correlacionados (não são 2 amostras independentes); DD pode subir.
"""

if __name__ == "__main__":
    for name, text in (("EXP-0017_orb-structural-relvolume", H17), ("EXP-0018_orb-structural-trend-aligned", H18), ("EXP-0019_orb-structural-second-entry", H19)):
        tools.start_experiment(name, text)
    start = datetime.now()
    clock = {"experimentation_start": start.isoformat(timespec="seconds"),
             "experimentation_deadline": (start + timedelta(minutes=20)).isoformat(timespec="seconds"),
             "setup_start": "2026-09-19T03:14:36"}
    (tools.RUN / "clock.json").write_text(json.dumps(clock, indent=1), encoding="utf-8")
    print("RELÓGIO DE EXPERIMENTAÇÃO INICIADO:", clock["experimentation_start"], "| prazo brando:", clock["experimentation_deadline"])
