# Unicidade de atividades.parquet: treinos em dobro (app × relógio)

Gerado por `src/unicidade_atividades.py`. Só leitura: `atividades.parquet` com SHA-256 `b5269feac894938c…` conferido antes e depois. Nada foi removido nem alterado.

## 1. Deslocamento de horário por origem (medido, não suposto)

Candidatos: mesma conta, mesmo tipo padronizado e mesma duração, um do `app` e um do relógio, **sem limite de tempo** além de ±24 h: 9.438. Para cada um, calculo `início do relógio − início do app`. Se uma origem grava o horário deslocado, os verdadeiros pares se concentram numa hora inteira; o resto se espalha.

### garmin: 5.223 candidatos

| deslocamento (h) | candidatos |
|---|---|
| 1 | 1 |
| 2 | 2 |
| 3 | 5.200 |
| 4 | 5 |

- Pico: **+3 h** (5.200 candidatos na hora inteira); 5.199 candidatos ficam a ≤ 5 min de +3 h, com mediana de **+3.000 h**. Fora do pico a contagem é residual (treinos parecidos em dias diferentes).

### apple_health: 4.215 candidatos

| deslocamento (h) | candidatos |
|---|---|
| -2 | 1 |
| -1 | 6 |
| 0 | 4.186 |
| 1 | 2 |
| 2 | 3 |

- Pico: **+0 h** (4.186 candidatos na hora inteira); 4.184 candidatos ficam a ≤ 5 min de +0 h, com mediana de **+0.000 h**. Fora do pico a contagem é residual (treinos parecidos em dias diferentes).

**Evidência resumida:** deslocamento medido = `garmin` +3 h; `apple_health` +0 h. A correção abaixo usa exatamente esses valores, subtraídos do início do relógio.

## 2. Pares sem e com correção do deslocamento

| origem do relógio | sem correção | com correção | diferença |
|---|---|---|---|
| garmin | 0 | 5.199 | 5.199 |
| apple_health | 4.184 | 4.184 | 0 |
| total | 4.184 | 9.383 | 5.199 |

Pares = um por treino, depois de desempatar (ver seção 4).

## 3. Pares por origem (com correção)

| par | pares |
|---|---|
| app com garmin | 5.199 |
| app com apple_health | 4.184 |

Soma por origem: **9.383** = total de pares ✔ (9.383).

## 4. Distância e treinos em mais de um par

- Distância também igual (ou as duas vazias): **9.383** de 9.383 (100.0%). Diferentes: 0.
- Antes de desempatar: 9.383 combinações dentro de 5 min; 0 delas envolvem um treino do app que casa com mais de um do relógio e 0 um do relógio que casa com mais de um do app. Desempate: o par de menor diferença de início, um par por treino.
- Depois do desempate: treinos do app em 2 pares = **0**; treinos do relógio em 2 pares = **0** ✔.

## 5. Cinco pares lado a lado (todas as colunas; `tipo_canon` é a cópia em memória)

### Par 1: app com garmin

| coluna | app | relógio |
|---|---|---|
| atividade_id | a_0452094 | a_0792276 |
| user_id | u_32beb9ff | u_32beb9ff |
| inicio | 2026-07-10 19:49:00 | 2026-07-10 22:49:00 |
| tipo | corrida | corrida |
| duracao_min | 35.7 | 35.7 |
| distancia_km | 5.17 | 5.17 |
| ritmo_min_km | 6.9 | 6.9 |
| fc_media | 163.0 | 163.0 |
| origem | app | garmin |
| gps_ok | True | True |
| treino_com |  |  |
| tipo_canon | corrida | corrida |
| diferença de início corrigida (min) | +0.0 |  |

### Par 2: app com garmin

| coluna | app | relógio |
|---|---|---|
| atividade_id | a_0180674 | a_0290176 |
| user_id | u_429d155a | u_429d155a |
| inicio | 2026-01-03 09:43:00 | 2026-01-03 12:41:00 |
| tipo | pedal | pedal |
| duracao_min | 80.1 | 80.1 |
| distancia_km | 38.6 | 38.6 |
| ritmo_min_km | 2.08 | 2.08 |
| fc_media | 136.0 | 136.0 |
| origem | app | garmin |
| gps_ok | True | True |
| treino_com |  |  |
| tipo_canon | pedal | pedal |
| diferença de início corrigida (min) | -2.0 |  |

### Par 3: app com garmin

| coluna | app | relógio |
|---|---|---|
| atividade_id | a_0357622 | a_0277949 |
| user_id | u_829ba3ce | u_829ba3ce |
| inicio | 2026-03-30 05:57:00 | 2026-03-30 08:55:00 |
| tipo | corrida | corrida |
| duracao_min | 42.0 | 42.0 |
| distancia_km | 6.85 | 6.85 |
| ritmo_min_km | 6.13 | 6.13 |
| fc_media | 156.0 | 156.0 |
| origem | app | garmin |
| gps_ok | True | True |
| treino_com |  |  |
| tipo_canon | corrida | corrida |
| diferença de início corrigida (min) | -2.0 |  |

### Par 4: app com apple_health

| coluna | app | relógio |
|---|---|---|
| atividade_id | a_0254159 | a_0731916 |
| user_id | u_be1f7d71 | u_be1f7d71 |
| inicio | 2026-07-05 08:49:00 | 2026-07-05 08:47:00 |
| tipo | corrida | corrida |
| duracao_min | 32.6 | 32.6 |
| distancia_km | 247.39 | 247.39 |
| ritmo_min_km | 5.89 | 5.89 |
| fc_media | 163.0 | 163.0 |
| origem | app | apple_health |
| gps_ok | True | True |
| treino_com |  |  |
| tipo_canon | corrida | corrida |
| diferença de início corrigida (min) | -2.0 |  |

### Par 5: app com apple_health

| coluna | app | relógio |
|---|---|---|
| atividade_id | a_0325728 | a_0957013 |
| user_id | u_fa6e0e16 | u_fa6e0e16 |
| inicio | 2026-03-01 08:58:00 | 2026-03-01 08:57:00 |
| tipo | pedal | pedal |
| duracao_min | 46.8 | 46.8 |
| distancia_km | 18.38 | 18.38 |
| ritmo_min_km | 2.55 | 2.55 |
| fc_media | 128.0 | 128.0 |
| origem | app | apple_health |
| gps_ok | True | True |
| treino_com |  |  |
| tipo_canon | pedal | pedal |
| diferença de início corrigida (min) | -1.0 |  |

## 6. Decisão proposta (formato do `decisoes.md`, não gravada)

| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |
|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|
| — | 09/11/2026 | atividades.parquet | 9.383 treinos registrados em dobro (app × relógio): mesma conta, tipo, duração, início ≤ 5 min com o deslocamento medido (garmin +3 h; apple_health +0 h) | remover da cópia tratada a linha do **app** de cada par e manter a do **relógio**; marcar `duplicata_app_relogio` se preferir manter a linha | o relógio traz `fc_media` (9.383 dos 9.383 pares têm frequência cardíaca no relógio) e o `inicio` com origem conhecida; 4.184 pares apareceriam sem a correção, 5.199 ficariam de fora | 1.254.475 → 1.245.092 (−9.383) |

Nota: reproduz a lógica da decisão 11; esta é a medição independente do deslocamento.

---
Conferência: 1.254.475 linhas lidas, nenhuma removida; `atividades.parquet` inalterado.