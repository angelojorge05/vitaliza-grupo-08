# Temporalidade de uso_mensal.csv: como o mês sem treino é registrado

Gerado por `src/temporalidade_uso_mensal.py`. Só leitura: SHA-256 conjunto de `uso_mensal.csv` e `usuarios.csv` `ceca1ce3f4a535aa…` conferido antes e depois. Nada foi corrigido.

## 1. Contagens do meio do caminho

- Linhas no arquivo: **591.662** (21 meses, de 2025-01 a 2026-09); soma das linhas por mês = total = dicionário ✔.
- Contas de teste (`@vitaliza.com.br` em `usuarios.csv`): **60**. Delas, **0** aparecem em `uso_mensal.csv` (0 linhas). Linhas depois de excluí-las: 591.662 → **591.662**.
- Soma das linhas por mês na tabela abaixo: **591.662**; a tabela cobre 21 meses ✔.
- Linhas repetidas para o mesmo `user_id` e mês: **0**.

## 2. Tabela por mês (sem as contas de teste)

"Arquivo" = todas as linhas como estão; ">0" = só as linhas com `minutos` > 0. Minutos em minutos por conta-mês.

| mês | linhas | contas | minutos = 0 | % zero | média (arquivo) | mediana (arquivo) | média (>0) | mediana (>0) | repetidas |
|---|---|---|---|---|---|---|---|---|---|
| 2025-01 | 11.441 | 11.441 | 0 | 0,0% | 299,9 | 168,0 | 299,9 | 168,0 | 0 |
| 2025-02 | 11.257 | 11.257 | 0 | 0,0% | 240,4 | 140,0 | 240,4 | 140,0 | 0 |
| 2025-03 | 12.005 | 12.005 | 0 | 0,0% | 267,6 | 153,0 | 267,6 | 153,0 | 0 |
| 2025-04 | 12.218 | 12.218 | 0 | 0,0% | 285,9 | 164,0 | 285,9 | 164,0 | 0 |
| 2025-05 | 12.419 | 12.419 | 0 | 0,0% | 296,5 | 166,0 | 296,5 | 166,0 | 0 |
| 2025-06 | 12.264 | 12.264 | 0 | 0,0% | 268,6 | 157,5 | 268,6 | 157,5 | 0 |
| 2025-07 | 12.460 | 12.460 | 0 | 0,0% | 272,1 | 159,0 | 272,1 | 159,0 | 0 |
| 2025-08 | 13.003 | 13.003 | 0 | 0,0% | 292,9 | 166,0 | 292,9 | 166,0 | 0 |
| 2025-09 | 13.452 | 13.452 | 0 | 0,0% | 294,3 | 171,0 | 294,3 | 171,0 | 0 |
| 2025-10 | 14.048 | 14.048 | 0 | 0,0% | 306,7 | 180,0 | 306,7 | 180,0 | 0 |
| 2025-11 | 14.039 | 14.039 | 0 | 0,0% | 296,9 | 173,0 | 296,9 | 173,0 | 0 |
| 2025-12 | 13.624 | 13.624 | 0 | 0,0% | 264,6 | 159,0 | 264,6 | 159,0 | 0 |
| 2026-01 | 41.130 | 41.130 | 25.697 | 62,5% | 117,9 | 0,0 | 314,2 | 179,0 | 0 |
| 2026-02 | 43.279 | 43.279 | 28.384 | 65,6% | 85,8 | 0,0 | 249,2 | 149,0 | 0 |
| 2026-03 | 45.309 | 45.309 | 29.658 | 65,5% | 94,1 | 0,0 | 272,3 | 158,0 | 0 |
| 2026-04 | 47.127 | 47.127 | 31.755 | 67,4% | 93,3 | 0,0 | 286,2 | 162,0 | 0 |
| 2026-05 | 48.909 | 48.909 | 33.832 | 69,2% | 91,2 | 0,0 | 295,9 | 174,0 | 0 |
| 2026-06 | 50.257 | 50.257 | 35.931 | 71,5% | 77,2 | 0,0 | 271,0 | 159,0 | 0 |
| 2026-07 | 52.234 | 52.234 | 37.959 | 72,7% | 74,4 | 0,0 | 272,3 | 160,0 | 0 |
| 2026-08 | 54.622 | 54.622 | 39.639 | 72,6% | 80,8 | 0,0 | 294,4 | 169,0 | 0 |
| 2026-09 | 56.565 | 56.565 | 40.880 | 72,3% | 82,6 | 0,0 | 298,0 | 173,0 | 0 |

## 3. A virada de 2025 para 2026

- **2025 (jan a dez):** 0 linhas com `minutos = 0` em 152.230. O mês sem treino **não aparece**: a conta simplesmente não tem linha. São 12.685 linhas por mês em média, todas de contas que treinaram.
- **2026 (jan a set):** 303.735 linhas com `minutos = 0` em 439.432 (69,1%). O mês sem treino **aparece como linha com zero**. As linhas por mês saltam de 13.624 (dez/2025) para 41.130 (jan/2026), e o salto é quase todo de zeros: as linhas com `minutos > 0` ficam em 12.685 por mês em 2025 e 15.077 em 2026, enquanto as linhas totais passam de 12.685 para 48.825.
- **Efeito na média do arquivo:** em 2025 ela é calculada só entre quem treinou (média de 282,2 min por mês); em 2026 entra o zero de quem não treinou e a média cai para 88,6 min, e a mediana vai a 0,0. A queda vem da forma de registrar, não do comportamento: o denominador mudou.
- **Mesma população?** Entre as linhas com `minutos > 0` o denominador é o mesmo nos dois anos (quem treinou no mês): média de 282,2 min em 2025 e 283,7 min em 2026.

## 4. Qual média comparar entre 2025 e 2026

- **Pode comparar:** a média e a mediana só sobre as linhas com `minutos > 0` (quem treinou no mês), porque nos dois anos medem o mesmo grupo.
- **Não pode comparar:** a média e a mediana sobre o arquivo como está. Em 2025 o denominador exclui quem não treinou; em 2026 o inclui. A diferença é de registro.
- Para olhar o mês sem treino em 2025 seria preciso reconstruir as linhas ausentes (conta com assinatura vigente e sem linha = zero), o que o arquivo sozinho não permite.

## 5. Decisão proposta (formato do `decisoes.md`, não gravada)

| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |
|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|
| — | 09/11/2026 | uso_mensal.csv | mês sem treino é linha ausente em 2025 e linha com `minutos = 0` em 2026 (303.735 zeros, 69,1% das linhas de 2026) | marcar `linha_zero` (minutos = 0) na cópia tratada; comparar 2025 e 2026 só com `minutos > 0`; não criar linhas de zero para 2025 sem a base de assinaturas | as médias do arquivo não são comparáveis entre os anos; remover os zeros de 2026 jogaria fora o dado de inatividade que só existe nesse ano | 591.662 linhas mantidas; 303.735 marcadas; 287.927 com `minutos > 0` para a comparação |

Contas de teste: 0 de 60 aparecem neste arquivo, então a exclusão não mudou nenhuma contagem.

---
Conferência: arquivos brutos inalterado.