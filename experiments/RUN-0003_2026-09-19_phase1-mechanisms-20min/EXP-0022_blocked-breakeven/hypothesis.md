# EXP-0022 — BLOCKED (capacidade do motor 1.1.0): breakeven / trailing com ativação condicional
Não rodado; NÃO conta como tentativa. Pai: RUN-0002/EXP-0011. Família: arquitetura de saída.
**hypothesis_source:** mecanismo (proteger lucro aberto após +1R reduz a fração de trades que devolvem o ganho e a dependência de poucos vencedores).
**Por que está BLOCKED:** o `ExitSpec` só tem trailing contínuo desde a entrada; não há limiar de ativação ("mover o stop para a entrada depois de +X pontos a favor"). Um proxy (trailing curto) já foi testado e é o oposto (EXP-0009/0010: whipsaw).
**Capacidade necessária (proposta D11):** campo de ativação condicional (ex.: `breakeven_after_points` / `trailing_activation_points`) com a mesma semântica conservadora (só barras fechadas; nunca na barra de entrada).
