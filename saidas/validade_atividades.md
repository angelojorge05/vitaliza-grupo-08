# Validade de atividades.parquet: distância e duração

## 1. Contagens

- Treinos: **1.254.475** (dicionário: 1.254.475).
- `distancia_km` preenchida: **679.640** (54.2%); vazia: **574.835** (45.8%). Vazio não é erro: a distância só existe quando há GPS.
- Conferência: 679.640 + 574.835 = 1.254.475 = total ✔.

## 2. Mínimo, mediana e máximo (só entre os preenchidos)

| coluna | preenchidos | mínimo | mediana | máximo |
|---|---|---|---|---|
| distancia_km | 679.640 | 0,00 | 6,47 | 10.012,75 |
| duracao_min | 1.254.475 | 0,00 | 41,40 | 543,90 |

## 3. Vazio, zero e impossível (casos separados)

| coluna | caso | treinos |
|---|---|---|
| distancia_km | vazio (sem GPS) | 574.835 |
| distancia_km | zero | 23 |
| distancia_km | negativa | 0 |
| distancia_km | > 200 km (impossível) | 951 |
| duracao_min | vazia | 0 |
| duracao_min | zero | 3.649 |
| duracao_min | negativa | 0 |

## 4. Treinos acima de 200 km por tipo e por origem

Por tipo (como gravado; `run`/`corrida` etc. são o mesmo tipo em inglês e português):

| tipo | treinos |
|---|---|
| corrida | 358 |
| run | 197 |
| caminhada | 152 |
| walk | 117 |
| pedal | 69 |
| ride | 58 |

Soma: 951.

Por tipo, forma canônica:

| tipo | treinos |
|---|---|
| corrida | 555 |
| caminhada | 269 |
| pedal | 127 |

Por origem:

| origem | treinos |
|---|---|
| app | 673 |
| garmin | 146 |
| apple_health | 132 |

Soma: 951.

Conferência: tipo = origem = 951 ✔.

## 5. Os cinco treinos de maior distância (todas as colunas)

| atividade_id | user_id | inicio | tipo | duracao_min | distancia_km | ritmo_min_km | fc_media | origem | gps_ok | treino_com |
|---|---|---|---|---|---|---|---|---|---|---|
| a_0719171 | u_01757952 | 2026-01-19 19:24:00 | pedal | 160.0 | 10012.75 | 2.54 | 121.0 | apple_health | True |  |
| a_0710325 | u_6f76aa66 | 2026-07-02 19:14:00 | ride | 190.6 | 8426.67 | 3.3 |  | app | True |  |
| a_1173215 | u_5e070f1e | 2026-03-25 21:38:00 | pedal | 294.3 | 8424.29 | 2.39 | 108.0 | garmin | True |  |
| a_0872023 | u_f9dd3384 | 2026-04-03 06:11:00 | pedal | 187.4 | 7986.38 | 3.33 |  | app | True |  |
| a_0309619 | u_f658c410 | 2026-07-11 07:39:00 | ride | 199.7 | 7871.13 | 3.25 |  | app | True |  |

## 5b. Os cinco treinos de maior duração (todas as colunas)

| atividade_id | user_id | inicio | tipo | duracao_min | distancia_km | ritmo_min_km | fc_media | origem | gps_ok | treino_com |
|---|---|---|---|---|---|---|---|---|---|---|
| a_0179347 | u_e9d1fc06 | 2026-02-06 06:42:00 | pedal | 543.9 | 160.81 | 3.38 | 151.0 | app | True |  |
| a_0749934 | u_eb40b0a9 | 2026-05-28 06:13:00 | pedal | 540.1 | 160.42 | 3.37 | 148.0 | apple_health | True |  |
| a_0591260 | u_0f9aa018 | 2026-01-13 06:00:00 | pedal | 536.6 | 162.04 | 3.31 |  | app | True |  |
| a_0927490 | u_15d12a18 | 2026-09-06 09:00:00 | pedal | 533.4 | 186.89 | 2.85 | 128.0 | garmin | True |  |
| a_0290007 | u_a1bd3ebe | 2026-07-18 06:12:00 | ride | 530.4 | 160.02 | 3.31 |  | app | True |  |

## 6. `gps_ok` x distância

| gps_ok | distância preenchida | distância vazia |
|---|---|---|
| False | 7455 | 7324 |
| True | 672185 | 567511 |

- `gps_ok` verdadeiro e distância vazia: **567.511**.
- `gps_ok` falso e distância preenchida: **7.455**.

Treinos com `gps_ok` verdadeiro e distância vazia, por tipo:

| tipo | treinos |
|---|---|
| forca | 198252 |
| funcional | 145476 |
| yoga | 113849 |
| hiit | 109934 |

## 7. Decisões propostas (não aplicadas)

| # | Problema | Decisão | Motivo | Efeito na contagem |
|---|---|---|---|---|
| a | `distancia_km` > 200 km | marcar (`flag_dist_impossivel`) e excluir dos agregados de engajamento; manter o bruto | fisicamente impossível; remover apagaria a atividade do histórico | 951 marcados; linhas: 1.254.475 → 1.254.475 |
| b | `distancia_km` vazia | manter vazia, sem marca de erro | dicionário: só existe com GPS | 574.835 vazios, 0 alterados |
| c | `distancia_km` zero ou negativa | marcar | zero: 23; negativa: 0 | 23 afetados |
| d | `duracao_min` zero ou negativa | marcar (`flag_dur_invalida`) | zero: 3.649; negativa: 0; duração vazia: 0 | 3.649 afetados |
| e | `gps_ok` verdadeiro e distância vazia | nada a fazer (não é problema) | todos são treinos sem percurso (forca, funcional, hiit, yoga); vazio esperado | 567.511 mantidos, 0 marcados |
| f | `gps_ok` falso e distância preenchida | marcar (`flag_gps_falso_com_distancia`) para conferir | distância gravada sem GPS confiável; não dá para provar erro | 7.455 marcados; linhas inalteradas |

Nenhuma decisão foi escrita em `decisoes.md`; depende da sua aprovação.

---
Conferência: 1.254.475 linhas lidas e nenhuma removida; `atividades.parquet` inalterado (SHA-256 `b5269feac894938c…`).