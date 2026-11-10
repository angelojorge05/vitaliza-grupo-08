# Preparação de atividades_limpa.parquet (decisões 9–12, ratificadas 08/11/2026)

Gerado por `src/preparar_atividades.py`. O bruto permanece intacto (SHA-256 `b5269feac894938c…` conferido antes e depois). O arquivo tratado fica em `dados/processados/` (fora do Git): cada colaborador o regenera rodando o script.

| Passo | Regra (decisão) | Efeito |
|---|---|---|
| 0 | Bruto lido | 1.254.475 treinos |
| 1 | `tipo` canônico (10) | 376.930 renomeadas; 11 → 7 categorias |
| 2 | `inicio` em Brasília | 207.954 inícios do garmin: UTC → −3h |
| 3 | Dedup app × relógio (11) | −9.383 registros do app; fica o do relógio (traz `fc_media`): 1.254.475 → 1.245.092 |
| 4 | `flag_impossivel` (9) | 4.573 marcados (944 >200 km, 3.631 duração ≤0); agregados usam 1.240.519 |
| 5 | `flag_outlier_iqr` (12) | 80.389 marcados (> 17.01 km); nada removido |

**Regra de uso:** toda análise, agregado ou feature por usuário parte de `atividades_limpa.parquet` filtrando `~flag_impossivel`; `flag_outlier_iqr` é informativa (os treinos longos de pedal são reais e ficam).
