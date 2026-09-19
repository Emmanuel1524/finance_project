# experiments/

Registro **versionado e imutável** da pesquisa de estratégias (Fase 1). Não é `outputs/` (gerado e ignorado pelo git): aqui ficam hipóteses, configurações, métricas e decisões — inclusive dos experimentos rejeitados. Regras completas: `docs/agentic_documentation/07_agent_protocol.md` §4–§6.

## Layout: um subdiretório por prompt-task (run)

```
experiments/
├── README.md
├── leaderboard.md                     # top 3 global + histórico de entradas/saídas (append-only)
└── RUN-0001_2026-09-19_<slug>/        # uma run = um prompt-task do usuário
    ├── run.md                         # prompt do usuário, orçamento (X minutos), início/fim,
    │                                  # commit git, versão do motor, hash e fronteiras dos dados,
    │                                  # Config-base (custos/slippage), nº de experimentos
    ├── EXP-0001_<slug>/
    │   ├── hypothesis.md              # hipótese + racional de mercado (escrito ANTES de rodar)
    │   ├── config.toml                # Config completa usada
    │   ├── metrics.json               # métricas, diagnósticos, IC, comparação com o V0
    │   └── decision.md                # blocos Integrity/Overfitting, KEEP/REJECT/REFINE, lições
    └── EXP-0002_<slug>/ ...
```

- `RUN-NNNN` é sequencial e nunca reutilizado; `EXP-NNNN` é sequencial **dentro da run** e o ID completo é `RUN-NNNN/EXP-NNNN`.
- **Nada é apagado nem reescrito.** Correções entram como nova entrada que referencia a anterior. Experimento rejeitado, inválido ou interrompido pelo limite de tempo permanece na sua pasta.
- Sair do top 3 tira o experimento do **placar**, não do registro.
- Baseline V0 e candidatos: cada `hypothesis.md` indica o **pai** (V0 ou outro candidato).
- Nenhum dado bruto ou de mercado é copiado para cá (só métricas e configurações); dados ficam em `data/`.
