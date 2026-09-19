# Análises B e C (não são tentativas; partição de pesquisa)

## B — placebo reforçado da arquitetura ORB estrutural (EXP-0011)
200 sorteios (sementes 5000–5199) de direção aleatória nos mesmos 100 instantes de entrada, mesma saída (stop no extremo oposto da 1ª barra, saída 17:55).
```
{
 "candidate_expectancy": 0.4,
 "draws": 200,
 "runtime_s": 45.7,
 "placebo_mean": -22.94,
 "placebo_sd": 14.05,
 "placebo_p5_p50_p95": [
  -46.6,
  -22.75,
  -0.98
 ],
 "placebo_max": 10.95,
 "P(placebo >= candidato)": 0.035,
 "z": 1.66
}
```
Leitura: o candidato (+R$ 0.4/trade) fica em z = 1.66 do acaso; P(placebo ≥ candidato) = 0.035. O sinal de direção supera o acaso com folga estatística.

## C — deriva intradiária da amostra (abertura 09:00 → fechamento 17:55), nos dias com sessão
```
{
 "days": 100,
 "mean_open_to_1755_pts": -2.4,
 "median": -6.07,
 "share_up": 0.42,
 "t_stat_mean": -0.65,
 "sum_pts": -239.7,
 "sd_pts": 37.15
}
```
Leitura: deriva não significativa (|t| < 2): a assimetria long/short observada NÃO é explicada por uma deriva intradiária estatisticamente detectável. Sem custos; em pontos de preço.
