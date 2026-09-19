import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools

D17 = """# EXP-0017 — decisão: REJECT (NÃO SUSTENTADO; o filtro escolheu trades piores que o típico)
Resultado: PF 0.856, WR 23.3%, PnL -R$546, DD 21.4%, 43 trades, payoff 2.83, expectância -R$12.7, meses + 2/5, top5 79%. Pai EXP-0011: exp. +R$0.4.
Placebo (20 sorteios, direção aleatória, mesma saída): média -R$34.2, p95 +R$8.35; excesso +R$21.5 (a arquitetura perde muito com direção aleatória; irrelevante para a comparação com o pai).
Placebo de SELEÇÃO (20.000 subconjuntos de 43 dos 100 trades do EXP-0011): P(acaso >= candidato) = 66% no PnL médio e 65% no PF => o filtro de volume relativo NÃO selecionou trades melhores que o acaso (mediana do acaso ≈ 0; candidato -12.7).
Integrity: Look-ahead PASS (volume da 1ª barra já fechada; mediana de sessões passadas) | Point-in-time PASS | Replay unchanged YES | New leakage risk NO | Leakage tests: auto-descoberta PASS (tests/test_candidates_auto_leakage.py)
Overfitting: hipótese estrutural YES (literatura+mecanismo, independente da amostra); micro-tuning NO (janela 20 e histórico 10 reusam o D7); complexidade justificada NO (sem ganho); estabilidade checada YES (2/5); concentração aceitável NO (79%, mas ver achado sobre o portão de concentração); validação consultada NO; premissa desafiada YES; placebo reportado YES
Lição: o mecanismo "in play" da literatura (ações/ETFs dos EUA) não se transfere ao WDO nesta amostra.
"""

D18 = """# EXP-0018 — decisão: REJECT (NÃO SUSTENTADO; piorou)
Resultado: PF 0.612, WR 13.7%, PnL -R$1867, DD 23.0%, 51 trades, payoff 3.85, expectância -R$36.6, meses + 1/5, top5 86%. LONG -R$227 / SHORT -R$1640.
Placebo (20 sorteios): média -R$41.4; excesso +R$4.8 (1 EP ≈ R$11+: ruído). Placebo de SELEÇÃO: P(acaso >= candidato) = 93% (PnL) e 90% (PF): o filtro escolheu trades PIORES que quase todos os subconjuntos aleatórios.
Integrity: Look-ahead PASS (EMAs D1 fechadas na abertura) | Point-in-time PASS | Replay unchanged YES | New leakage risk NO | Leakage tests: auto-descoberta PASS
Overfitting: hipótese estrutural YES (mecanismo, independente); micro-tuning NO; complexidade justificada NO; estabilidade checada YES (1/5); concentração aceitável NO; validação consultada NO; premissa desafiada YES; placebo reportado YES
Lição: o alinhamento com a tendência D1 (reaberto agora para continuação) também não sustenta; o EXP-0004 (fades) e este (continuação) convergem: a tendência D1 não é um filtro útil nesta amostra.
"""

D19 = """# EXP-0019 — decisão: REJECT (NÃO SUSTENTADO; piora drawdown e resultado)
Resultado: PF 0.905, WR 18.2%, PnL -R$987, DD 34.89% (reprova), 121 trades (100 iniciais + 21 re-entradas), payoff 4.07, expectância -R$8.16, meses + 3/5, 20 perdas seguidas.
As 21 re-entradas (ORB_STRUCT_RE): -R$1027, WR 14.3%. Os 100 primeiros trades reproduzem exatamente o EXP-0011 (+R$40).
Placebo (20 sorteios): média -R$16.96, p95 +R$3.1; excesso +R$8.8 (< 1 EP). Placebo de seleção: n/a (trades não são subconjunto da arquitetura-base).
Integrity: Look-ahead PASS (stop-out inferido só de barras fechadas, mesma regra do motor; re-entrada por fechamento de barra) | Point-in-time PASS | Replay unchanged YES (max_trades_per_day=2 é Config do candidato) | New leakage risk NO | Leakage tests: auto-descoberta PASS (leakage_config max_trades_per_day=2)
Overfitting: hipótese estrutural YES (mecanismo); micro-tuning NO; complexidade justificada NO; estabilidade checada YES; concentração aceitável NO; validação consultada NO; premissa desafiada YES (limite de 1 trade/dia, D9); placebo reportado YES
Lição: recuperação de rompimento falho não agrega; re-entrada correlaciona perdas no mesmo dia (não são amostras independentes). Família multi-trade: 1 rejeição.
"""

H20 = """# EXP-0020 — ORB de 5 min na ABERTURA DE NOVA YORK (09:30 ET), stop estrutural, saída 17:55
Pai: RUN-0002/EXP-0011 (mesma arquitetura, outro instante). Ramo: Opening-Momentum. Família: momentum na abertura dos EUA.
**Checagem de novidade:** o ORB só foi testado na abertura da B3 (09:00 BRT). Abertura de NY nunca testada.
**hypothesis_source:** literatura (sazonalidade intradiária da volatilidade em câmbio: pico na abertura de Londres/NY, Andersen & Bollerslev 1997; Ito & Hashimoto 2006) + mecanismo (o dólar/real reage à abertura dos EUA: dados e fluxo entram nesse instante). INDEPENDENTE da amostra.
**Premissa desafiada:** que a única janela relevante seja a abertura da B3 (09:00–10:30); janela livre (D9).
**Reabertura:** — (janela nova; arquitetura da fronteira).
**Hipótese:** o corpo da 1ª barra de 5 min a partir de 09:30 ET (10:30 BRT no horário de verão dos EUA, 11:30 BRT fora dele; o DST dos EUA começou em 2026-03-08 e a conversão é feita pelo fuso America/New_York) prediz a continuação; entrada na abertura da barra seguinte, stop no extremo oposto da barra, sem alvo, saída 17:55.
**Os 4 pontos (sem parâmetro alterado):** (i) a B3 abre sem os EUA; o fluxo dos EUA chega às 09:30 ET; (ii) mesma regra do EXP-0011 aplicada à barra das 09:30 ET; janela de sessão 09:00–12:00 BRT (Config do candidato) só para a estratégia enxergar as barras; (iii) outra janela do dia (construto: abertura dos EUA), não vizinho numérico; (iv) sustenta: expectância > 0 e acima do placebo com portões OK; rejeita: caso contrário.
Graus de liberdade: 0. Risco: tratamento de DST (feito por tz_convert, point-in-time); série ajustada (R6).
"""

H21 = """# EXP-0021 — ORB estrutural (EXP-0011) com ALVO ESTRUTURAL no extremo do dia anterior (PDH/PDL)
Pai: RUN-0002/EXP-0011. Ramo: Opening-Momentum. Família: arquitetura de saída (alvo estrutural).
**Checagem de novidade:** alvos FIXOS (6 e 20 pts) foram testados (EXP-0002/0003, NÃO SUSTENTADOS); alvo por ESTRUTURA nunca.
**hypothesis_source:** mecanismo (níveis de extremo do dia anterior concentram liquidez/ordens; realizar o lucro neles reduz a dependência de poucos trades grandes, a fragilidade do EXP-0011/0012). Independente da amostra.
**Premissa desafiada:** ausência de alvo (positive skew puro, top-5 ≈ 56–72% do lucro).
**Reabertura:** (i) mecanismo novo — alvo definido por estrutura, não por distância fixa.
**Hipótese:** com stop no extremo oposto da 1ª barra e alvo no extremo do dia anterior na direção do trade (PDH para compra, PDL para venda) quando esse nível estiver a pelo menos 2 pts da abertura (senão, sem alvo), a win rate sobe e a concentração cai sem destruir a expectância.
**Os 4 pontos (sem parâmetro numérico novo):** (i) sem alvo, poucos vencedores grandes dominam o lucro; (ii) `target_price` = PDH/PDL conhecido na abertura; (iii) muda a arquitetura de saída por estrutura, não é vizinho de alvo fixo; (iv) sustenta: expectância > 0 e acima do placebo com menor concentração; rejeita: caso contrário.
Graus de liberdade: 0 (a margem de 2 pts é guarda de validade do alvo). Nota: PDH/PDL vêm da série ajustada (R6).
"""

if __name__ == "__main__":
    for d, text in (("EXP-0017_orb-structural-relvolume", D17), ("EXP-0018_orb-structural-trend-aligned", D18), ("EXP-0019_orb-structural-second-entry", D19)):
        tools.write_decision(tools.RUN / d, text)
        m = tools.load_metrics(tools.RUN / d / "metrics.json")
        src = {"EXP-0017": "literatura+mecanismo", "EXP-0018": "mecanismo", "EXP-0019": "mecanismo"}[d[:8]]
        fam = {"EXP-0017": "participation-filter", "EXP-0018": "trend-alignment", "EXP-0019": "multi-trade"}[d[:8]]
        chall = {"EXP-0017": "trade every day", "EXP-0018": "both sides regardless of trend", "EXP-0019": "1 trade/day limit"}[d[:8]]
        n = int(d[6:8]) - 16 if False else int(d[4:8]) - 16
        tools.add_registry(tools.registry_row2(d[:8], "RUN-0002/EXP-0011", "Opening-Momentum", fam, d, d, "REJECT", m, src, chall, "(i) new mechanism", 0, n))
    for name, text in (("EXP-0020_orb-ny-open", H20), ("EXP-0021_orb-structural-pdh-target", H21)):
        tools.start_experiment(name, text)
    import datetime
    print("HIPÓTESES DO LOTE 2 REGISTRADAS:", datetime.datetime.now().isoformat(timespec="seconds"))
