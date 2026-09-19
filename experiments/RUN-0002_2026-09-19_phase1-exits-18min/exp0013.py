import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from wdo.strategies.candidates_run2 import OpeningRange30Breakout

D12 = """# EXP-0012 — decisão: INCONCLUSIVE (data-informed; melhor resultado, MAS reprova nos portões de concentração)
Resultado: PF 1.414, WR 28.9%, PnL +R$1530, DD 14.26% (passa), 45 trades, payoff 3.48, expectância +R$34.0, meses + 3/5 (fev -445, mar +1788, abr -203, mai +258, jun +132).
Placebo (10 sorteios com o MESMO gate): média -R$41.7, p95 -R$25.2, máx -R$0.11: candidato acima de TODOS os sorteios (excesso +R$75.7/trade).
Portões D3: min_trades OK; DD OK (14.26%); expectância OK; FALHAM top5 trades = 72% do lucro bruto (> 40%) e concentração mensal (março +1788 > lucro total +1530: sem março o resultado é negativo, -R$258).
Interpretação: sinal consistente com o placebo, mas dependente de poucos trades e de um mês; a regra de regime veio da MESMA amostra que a testa (snooping: 4 leituras + esta). Não elegível ao placar. Candidato a checkpoint de validação (consome 1 das 3): decisão do usuário.
Integrity: Look-ahead PASS | Point-in-time PASS (mediana de 20 pregões passados, D7) | Replay unchanged YES | New leakage risk NO | Leakage tests: pendente até o fim da run
Overfitting: hipótese estrutural YES (com ressalva data-informed); micro-tuning NO; complexidade justificada YES (0 dof); estabilidade checada YES (frágil); concentração aceitável NO; validação consultada NO; premissa desafiada YES; placebo reportado YES
"""

H = """# EXP-0013 — Rompimento do range de abertura de 30 min (09:00–09:30), stop estrutural, saída 17:55
Pai: V0 (família nova; sem linha equivalente em knowledge.md). Ramo: Opening-Range-Breakout-30. Família: rompimento de range.
**hypothesis_source:** literatura (opening range breakout em futuros de índice — TORB; Zarattini & Aziz 2023 generaliza o ORB) + mecanismo (rompimento confirmado por barra fechada filtra ruído da 1ª barra).
**Premissa do V0 desafiada:** entrada por fade/1ª barra e saída fixa 10/6; janela e limite diário mantidos (09:30–10:30 para entrar, 1 trade/dia).
**Hipótese:** o rompimento fechado do range de 30 min (e não o corpo de uma barra de 5 min) captura continuação mais robusta; stop no extremo oposto do range e posição mantida até 17:55.
**Os 4 pontos (sem parâmetro alterado):** (i) o corpo de UMA barra é um sinal ruidoso; (ii) range 09:00–09:25, rompimento por fechamento de barra, entrada na abertura seguinte, stop estrutural oposto, sem alvo, saída por horário; (iii) construto diferente (range vs barra), não vizinho numérico; (iv) sustenta: expectância > 0 e acima do placebo com portões OK; rejeita: caso contrário.
Graus de liberdade: 0 (o range de 30 min é o construto, escolhido a priori pela literatura).
"""

if __name__ == "__main__":
    tools.write_decision(tools.RUN / "EXP-0012_orb-structural-volgate", D12)
    m12 = tools.load_metrics(tools.RUN / "EXP-0012_orb-structural-volgate" / "metrics.json")
    tools.add_registry(tools.registry_row2("EXP-0012", "EXP-0011", "Opening-Momentum", "momentum+regime",
                       "ORB structural only in high-vol regime (D7)", "EXP-0011 + stand_down in low-vol", "INCONCLUSIVE", m12,
                       "decomposição (data-informed)+mecanismo", "trade every day", "(i) new mechanism (gate with adaptive exit)", 0, 4))
    tools.run_experiment2("EXP-0013", "or30-breakout", OpeningRange30Breakout, H,
                          {"strategy": "OpeningRange30Breakout", "range": "09:00-09:30", "exit": "opposite side of range, no target, exit_time 17:55", "dof": 0}, tools.load_metrics(tools.RUN / "EXP-0000_baseline-v0" / "metrics.json"))
