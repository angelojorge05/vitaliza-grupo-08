# Diagnóstico do onboarding (Passo 1, só leitura)

## `dias_por_semana`: formas encontradas

23 formas distintas (incluindo o vazio).

| Forma | Linhas |
|---|---:|
| `3` | 10.268 |
| `2` | 7.576 |
| `4` | 7.437 |
| `(vazio)` | 6.368 |
| `5` | 3.649 |
| `3 vezes` | 3.450 |
| `3x` | 3.443 |
| `1` | 2.671 |
| `2x` | 2.558 |
| `4 vezes` | 2.557 |
| `4x` | 2.452 |
| `2 vezes` | 2.443 |
| `5 vezes` | 1.276 |
| `5x` | 1.254 |
| `6` | 1.128 |
| `1x` | 925 |
| `todos` | 917 |
| `1 vezes` | 906 |
| `7` | 798 |
| `6 vezes` | 549 |
| `6x` | 527 |
| `7x` | 395 |
| `7 vezes` | 382 |

## Espaços nas pontas e caixa

| Coluna | Com espaço nas pontas | Valores que diferem só pela caixa |
|---|---:|---:|
| `nivel` | 0 | 0 |
| `dias_por_semana` | 0 | 0 |
| `objetivo_texto` | 0 | 0 |
| `como_conheceu` | 0 | 0 |

## `respondido_em`: formatos

| Formato (9 = dígito) | Linhas |
|---|---:|
| `9999-99-99` | 63.929 |

- Datas que não leem como `AAAA-MM-DD`: **0**.
- Datas depois do corte (30/09/2026): **0**.
- Intervalo: 2020-09-01 a 2026-09-30.

## Cobertura e duplicatas

- `usuarios.csv`: 64.948 linhas, 64.948 `user_id` únicos, **0 duplicados**.
- `onboarding.csv`: 63.929 linhas, 63.929 `user_id` únicos, **0 duplicados**.
- Contas de `usuarios.csv` sem linha no onboarding: **1.019**.
- `user_id` do onboarding que não existem em `usuarios.csv`: **0**.

SHA-256 de `onboarding.csv` e `usuarios.csv` igual antes e depois: o bruto não foi tocado.
