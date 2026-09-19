# AGENTS.md — instruções para agentes (Codex e outros)

Projeto quant em Python: backtest/replay de um EA MQL5 de abertura do WDO (B3). Objetivo: estratégia produtizável, sólida e escalável.

**Leia primeiro:** `docs/agentic_documentation/README.md` (índice), depois `docs/agentic_documentation/07_agent_protocol.md`. Regras detalhadas: `CLAUDE.md` (mesmo conteúdo de conduta, escrito para Claude Code).

## Regras essenciais

1. Fonte da verdade das regras da estratégia: `reference/mt5/Robo_Abertura_WDO_Genial_v1.35.mq5` (MQL5). O Python (`src/wdo/`) deve espelhá-lo.
2. Nunca introduzir look-ahead: em `t` só se usa informação disponível em ou antes de `t`; sinal calculado com o close da barra t só executa a partir de t+1; timing ambíguo ⇒ premissa conservadora. Todo indicador/feature novo: revisão point-in-time e testes de vazamento (`docs/agentic_documentation/05` §5 e §11).
3. Manter `intrabar_policy="adverse"` como padrão. Nunca ajustar premissas para melhorar resultado.
4. Custos, slippage e valor do ponto sempre explícitos em qualquer resultado.
5. Parâmetros só em `Config`. Dados brutos (`data/raw/wdo_data.csv`) são imutáveis.
6. Rodar `pytest -q` e reportar o resultado **real**. Nunca inventar métricas; diferenciar "verificado" de "inferido".
7. Não instalar dependências, não commitar fora do autorizado (apenas o registro de cada run, uma vez ao fim do prompt-task), não apagar arquivos e não mudar defaults conservadores sem pedir.
8. Responder ao usuário em **português (pt-BR)**.
9. **Portão de pesquisa:** a Fase 1 (descoberta de estratégia) não está autorizada. Sem aprovação explícita: não rodar backtests de pesquisa, não alterar a estratégia, não otimizar parâmetros, não tocar validação/holdout. Depois de autorizada: hipótese explícita → replay → KEEP/REJECT/REFINE, orçamento finito, registro imutável de todos os experimentos, motor de replay congelado (ver `docs/agentic_documentation/06`, `07`, `05 §10`).
10. Ao terminar, escrever um handoff (formato em `07_agent_protocol.md`).

## Comandos (PowerShell, Windows)

**Ambiente obrigatório: conda `wdo-backtest`** (`environment.yml`; kernel Jupyter "Python (wdo-backtest)"). Não use o `.venv` (obsoleto). Para rodar o notebook headless, use o `nbconvert` do próprio ambiente (ver `docs/agentic_documentation/README.md`).

```powershell
conda activate wdo-backtest
pytest -q
```
