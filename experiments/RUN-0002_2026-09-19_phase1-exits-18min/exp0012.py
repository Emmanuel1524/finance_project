import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from wdo.strategies.candidates_run2 import OrbStructuralVolGate

D11 = """# EXP-0011 — decisão: REFINE (uma mudança estrutural específica: filtro de regime; ver EXP-0012), NÃO qualificado nos portões
Resultado: PF 1.005, WR 19%, PnL +R$40, DD 24.63%, 100 trades, payoff 4.29, expectância +R$0.4, meses + 3/5 (fev -1714, mar +1206, abr -565, mai +1045, jun +68), top5 55.7%, pior trade -R$267, 17 perdas seguidas.
Placebo (10 sorteios): média -R$25.98, p95 -R$9.1, máx +R$2.9; excesso +R$26.4/trade. Acima do p95, mas um sorteio de 10 supera o candidato e o erro-padrão da expectância (~R$11) é maior que a expectância: indistinguível de zero e do acaso.
Reprova: DD 24.6% > 15%; top5 55.7% > 40%; concentração mensal (mar/mai dominam). LONG +850 vs SHORT -810 (viés direcional da amostra).
Padrão replicado (mesma amostra): baixa vol perde em V0, EXP-0009, 0010, 0011 (-1125, -1044, -794, -939); alta vol: +28, +54, -201, +979.
Integrity: Look-ahead PASS (extremos da 1ª barra fechada; guarda de gap) | Point-in-time PASS | Replay unchanged YES | New leakage risk NO | Leakage tests: pendente até o fim da run
Overfitting: hipótese estrutural YES (literatura); micro-tuning NO; complexidade justificada YES (0 dof); estabilidade checada YES (frágil); concentração aceitável NO; validação consultada NO; premissa desafiada YES; placebo reportado YES
"""

H = """# EXP-0012 — ORB estrutural (EXP-0011) só em regime de volatilidade alta
Pai: EXP-0011. Ramo: Opening-Momentum. Família: momentum + arquitetura de saída + regime.
**hypothesis_source:** decomposição (DATA-INFORMED) reforçada por mecanismo: em dias de baixo range o movimento é pequeno frente a custo/slippage e à distância do stop; a continuação da 1ª barra precisa de range para se pagar. Literatura de regimes de volatilidade (fontes fracas) e Gao et al. 2018 (momentum mais forte em dias voláteis) apontam no mesmo sentido.
**Premissa desafiada:** operar todos os dias com a mesma arquitetura.
**Reabertura:** (i) mecanismo novo: o filtro de volatilidade (EXP-0001) só foi testado com saída fixa (NÃO SUSTENTADO); aqui atua sobre uma arquitetura de saída adaptada ao momentum.
**Hipótese:** restringir ao regime de alta volatilidade (D7, definição fixa) eleva a expectância e reduz drawdown sem novo parâmetro.
**Os 4 pontos:** (i) baixa vol perdeu em 4 arquiteturas; (ii) skip quando range do dia anterior <= mediana dos 20 pregões (D7); (iii) filtro de regime sobre arquitetura nova, não vizinho numérico; (iv) sustenta: expectância > 0 e acima do placebo, DD/concentração dentro dos portões com >= 30 trades; rejeita: caso contrário.
Graus de liberdade: 0 (D7 fixo). RISCO: a mesma amostra sugeriu e agora testa a regra (snooping): qualquer aprovação exige checkpoint de validação; n esperado ~45 (limítrofe).
"""

if __name__ == "__main__":
    tools.write_decision(tools.RUN / "EXP-0011_orb-structural-stop", D11)
    m11 = tools.load_metrics(tools.RUN / "EXP-0011_orb-structural-stop" / "metrics.json")
    tools.add_registry(tools.registry_row2("EXP-0011", "EXP-0010", "Opening-Momentum", "momentum+exit-architecture",
                       "ORB with literature exit: structural stop, no trailing, EOD exit", "ExitSpec stop_price=1st bar extreme, exit 17:55", "REFINE", m11,
                       "literatura", "trailing/stop derived from V0", "(i) new mechanism", 0, 3))
    tools.run_experiment2("EXP-0012", "orb-structural-volgate", OrbStructuralVolGate, H,
                          {"strategy": "OrbStructuralVolGate", "gate": "D7 range prev day > median 20", "dof": 0}, m11)
