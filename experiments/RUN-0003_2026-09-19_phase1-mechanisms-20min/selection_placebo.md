# Análise A — placebo de seleção do filtro de volatilidade (EXP-0012)  [não é tentativa]

Método: 20,000 subconjuntos aleatórios (sem reposição, semente fixa) de 45 dos 100 trades do EXP-0011 (arquitetura sem filtro), comparados com o EXP-0012 (os mesmos trades sob o filtro D7 de alta volatilidade). Os 45 trades do EXP-0012 são um subconjunto dos do EXP-0011: **True**.

| Métrica | EXP-0012 (observado) | Acaso: p5 / mediana / p95 | P(acaso ≥ observado) |
|---|---|---|---|
| PnL médio por trade (R$) | 34.0 | -45.556 / 0.222 / 47.556 | **0.123** |
| Profit Factor | 1.41 | 0.475 / 1.003 / 1.658 | **0.145** |
| Top-5 trades / lucro bruto | 0.72 | 0.698 / 0.836 / 1.000 (corrigido: 1 subconjunto em 20.000 sem vencedores gerava NaN) | 0.910 |

**Leitura.** A probabilidade de uma seleção ao acaso (do mesmo tamanho, dentro dos trades da própria arquitetura) igualar o PnL médio do EXP-0012 é **12.3%**; a do PF é 14.5%. Isso mede a sorte de *selecionar* dias, não a de a arquitetura ter edge. A regra de volatilidade (D7) foi escolhida DEPOIS de ver a decomposição na mesma amostra (data-informed), então mesmo uma probabilidade baixa não a torna evidência independente; e a concentração (top-5 = 72% do lucro bruto) é esperada para subconjuntos deste tamanho (P = 0.91).

## Item 4 — diagnósticos (long/short e metades do período de pesquisa)
```
{
 "EXP-0011": {
  "long": {
   "n": 50,
   "pnl": 850.0
  },
  "short": {
   "n": 50,
   "pnl": -810.0
  },
  "1a metade": {
   "n": 51,
   "pnl": -442.0
  },
  "2a metade": {
   "n": 49,
   "pnl": 482.0
  }
 },
 "EXP-0012": {
  "long": {
   "n": 24,
   "pnl": 562.0
  },
  "short": {
   "n": 21,
   "pnl": 968.0
  },
  "1a metade": {
   "n": 22,
   "pnl": 1251.0
  },
  "2a metade": {
   "n": 23,
   "pnl": 279.0
  }
 }
}
```
Nota: assimetria long/short e diferença entre metades **sem mecanismo independente** não geram hipótese nesta run (seriam decomposição).

## Correção e achado metodológico (registrado no fim da Análise A)
- A primeira versão imprimiu NaN nos percentis do top-5 (um subconjunto sem nenhum trade vencedor contaminava `np.percentile`); os valores corretos estão na tabela. Os p-valores não mudaram.
- **Achado:** em subconjuntos aleatórios de 45 trades desta arquitetura o top-5 típico é **0,84** do lucro bruto (p5 = 0,70): a concentração de 72% do EXP-0012 é **normal**, não um defeito do filtro. Motivo estrutural: win rate ~19% com payoff ~4 ⇒ poucos vencedores (≈ 13 em 45), então os 5 maiores dominam qualquer subconjunto. **O portão D3 "top-5 ≤ 40% do lucro bruto" é, na prática, inatingível para arquiteturas de win rate baixo e payoff alto.** Não altero o portão (é fixo e exige o usuário); registro como decisão pendente D10 e uso o percentil do placebo de seleção como leitura complementar.
- **Peso do EXP-0012:** P(seleção ao acaso ≥ +R$34/trade) = 12,3% (PF: 14,5%): moderado, não conclusivo; a regra é data-informed. Sem novas hipóteses derivadas de long/short ou de metades (sem mecanismo independente).
