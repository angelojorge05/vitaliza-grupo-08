# Limpeza de outliers de atividades

Gerado por `src/limpar_outliers_atividades.py`. Saída: `dados/processados/atividades_limpa_v2.parquet` (fora do Git). Bruto inalterado (SHA-256 `b5269feac894938c…`).
Valores originais ficam em `distancia_km_original` e `ritmo_min_km_original`; cada anulação tem sua marca (`dist_anulada_acima_200km`, `dist_anulada_gps_falso`, `dist_anulada_zero`).

| Passo | Efeito | Contagem |
|---|---|---|
| 0. Entrada (atividades_limpa, decisões 9-12) | 1.245.092 treinos | 674.506 com distância |
| 1. Remove duração <= 0 | -3.631 treinos (zero: 3.631; negativa: 0) | 1.245.092 → 1.241.461 |
| 2. Anula distância > 200 km (e ritmo) | 942 distâncias anuladas | linhas: 1.241.461 |
| 3. Anula distância com gps_ok falso (e ritmo) | 7.435 distâncias anuladas | linhas: 1.241.461 |
| 4. Anula distância 0 em tipo com GPS (e ritmo) | 0 anuladas; 0 zeros em outros tipos mantidos | linhas: 1.241.461 |
| 5. flag_outlier_iqr recalculada (> 17.12 km, só informativa) | 79.836 marcados, 0 removidos | linhas: 1.241.461 |

- Linhas finais: **1.241.461** (entrada 1.245.092 − 3.631 de duração ≤ 0). Distância preenchida: 674.506 → 664.149. Distância máxima: 198.69 km.
- Ritmo preenchido com distância vazia depois da limpeza: 0.
- A marca `flag_impossivel` da v1 sai da v2: os impossíveis foram removidos ou anulados.
- Não limpo, de propósito: os 79.836 treinos acima do IQR (pedais longos e plausíveis) e as durações altas (máx. 543,9 min).

## Decisões 23 a 27 (gravadas no `decisoes.md` em 09/11/2026)

| # | Data | Arquivo | Problema | Decisão | Motivo | Efeito |
|---|---|---|---|---|---|---|
| 23 | 09/11/2026 | atividades.parquet | duração ≤ 0 | remover da cópia v2 (substitui a marca da decisão 9 para duração) | treino de 0 min não aconteceu | -3.631 treinos: 1.245.092 → 1.241.461 |
| 24 | 09/11/2026 | atividades.parquet | distância > 200 km | anular `distancia_km` e `ritmo_min_km`, manter o treino (substitui a marca da decisão 9 para distância) | fisicamente impossível, mas o treino existe | 942 anuladas; linhas inalteradas |
| 25 | 09/11/2026 | atividades.parquet | `gps_ok` falso com distância | anular `distancia_km` e `ritmo_min_km`, manter o treino | dicionário: distância só existe com GPS | 7.435 anuladas |
| 26 | 09/11/2026 | atividades.parquet | distância vazia com `gps_ok` verdadeiro (força, funcional, yoga, HIIT) e distância 0 em tipo com GPS (0 após a 23) | manter, sem marca de erro | vazio esperado em treino sem percurso | 0 alterados |
| 27 | 09/11/2026 | atividades.parquet | acima de Q3+1,5×IQR (pedais longos) | marcar apenas (`flag_outlier_iqr` recalculada) | longos porém plausíveis; mantém a decisão 12 | 79.836 marcados (> 17,12 km); 0 removidos |
