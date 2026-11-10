# Churn mensal oficial, jan/2025 a set/2026

Gerado por `src/churn_mensal.py`. Só leitura (SHA-256 conjunto de `assinaturas.csv`, `eventos_assinatura.csv` e `usuarios.csv` `0feacc5fa962a6fe…` conferido antes e depois).

Definição: churn do mês = perdas no mês ÷ ativos no início do mês. Ativo no início = `inicio` antes do dia 1 e (sem `data_fim` ou `data_fim` ≥ dia 1). Perda = ativo no início com `data_fim` dentro do mês. Assinaturas que começam e terminam no mesmo mês ficam fora.

## 1. Linhas depois de cada passo

| passo | linhas | observação |
|---|---|---|
| assinaturas.csv | 32.643 | 32.643 user_id únicos |
| sem as 60 contas de cortesia/teste (decisão 1) | 32.583 | cortesia 60, teste por e-mail 60, ambos 60 |

- Datas inválidas: `inicio` 0; `data_fim` 0; `data_fim` antes de `inicio`: 0.

## 2. Série mensal (21 meses)

| mês | ativos no início | perdas | churn | novos no mês | começam e acabam no mês | renovação desligada | falha de pagamento | chargeback | reembolso |
|---|---|---|---|---|---|---|---|---|---|
| 2025-01 | 8.540 | 534 | 6,3% | 1.423 | 11 | 495 | 33 | 5 | 1 |
| 2025-02 | 9.418 | 529 | 5,6% | 1.134 | 9 | 475 | 44 | 9 | 1 |
| 2025-03 | 10.014 | 552 | 5,5% | 1.122 | 7 | 504 | 45 | 3 | 0 |
| 2025-04 | 10.577 | 522 | 4,9% | 886 | 4 | 478 | 38 | 5 | 1 |
| 2025-05 | 10.937 | 543 | 5,0% | 931 | 8 | 490 | 47 | 2 | 4 |
| 2025-06 | 11.317 | 562 | 5,0% | 888 | 3 | 508 | 43 | 7 | 4 |
| 2025-07 | 11.640 | 679 | 5,8% | 857 | 7 | 609 | 61 | 5 | 4 |
| 2025-08 | 11.811 | 774 | 6,6% | 989 | 6 | 709 | 58 | 3 | 4 |
| 2025-09 | 12.020 | 704 | 5,9% | 1.103 | 6 | 659 | 39 | 3 | 3 |
| 2025-10 | 12.413 | 742 | 6,0% | 1.106 | 6 | 675 | 61 | 1 | 5 |
| 2025-11 | 12.771 | 723 | 5,7% | 978 | 3 | 662 | 56 | 3 | 2 |
| 2025-12 | 13.023 | 695 | 5,3% | 816 | 4 | 619 | 61 | 5 | 10 |
| 2026-01 | 13.140 | 959 | 7,3% | 1.561 | 14 | 897 | 58 | 3 | 1 |
| 2026-02 | 13.728 | 830 | 6,0% | 1.219 | 6 | 757 | 58 | 11 | 4 |
| 2026-03 | 14.111 | 989 | 7,0% | 1.131 | 16 | 902 | 78 | 4 | 5 |
| 2026-04 | 14.237 | 1.154 | 8,1% | 1.040 | 4 | 1.071 | 71 | 6 | 6 |
| 2026-05 | 14.119 | 1.026 | 7,3% | 1.021 | 12 | 953 | 64 | 5 | 4 |
| 2026-06 | 14.102 | 866 | 6,1% | 832 | 9 | 797 | 58 | 7 | 4 |
| 2026-07 | 14.059 | 948 | 6,7% | 930 | 9 | 885 | 57 | 3 | 3 |
| 2026-08 | 14.032 | 834 | 5,9% | 1.127 | 6 | 765 | 59 | 8 | 2 |
| 2026-09 | 14.319 | 714 | 5,0% | 1.151 | 3 | 628 | 72 | 11 | 3 |

Perdas por motivo somam as perdas de cada mês: ✔ (motivos fora da lista: 0).

## 3. Conferência com o case

| medida | referência do case | calculado |
|---|---|---|
| ativos no início de jan/2025 | 8.540 | 8.540 |
| churn médio 2025 (média simples dos 12 meses) | 5,6% | 5,6% |
| churn médio jan–set/2026 (média simples) | 6,6% | 6,6% |
| abril/2026: perdas sobre ativos | 1.154 sobre 14.237 (8,1%) | 1.154 sobre 14.237 (8,1%) |
| agosto/2026 | 5,9% | 5,9% |
| setembro/2026 | 5,0% | 5,0% |
| ativos no início de set/2026 | 14.319 | 14.319 |
| perdas jun a set (série) | 3.362 | 3.362 |
| fins de assinatura jun a set | 3.389 | 3.389 |
| ativos em 30/09/2026 | 14.753 | 14.753 |

- Churn ponderado (perdas ÷ ativos somados): 2025 5,6%; jan–set/2026 6,6%.
- Diferença entre fins e perdas de jun a set: 27 (assinaturas que começam e terminam no mesmo mês: 27).

## 4. Conferência com os eventos (desde 01/07/2024, fuso em Brasília)

Para cada assinatura encerrada com `data_fim` desde 01/07/2024 (17.830), comparo `data_fim` com o último evento de fim (`assinatura_expirada`, `chargeback` ou `reembolso`; `cancelamento_web` não conta, decisão 15).

| motivo_fim | encerradas | mesmo dia | mesmo mês, outro dia | outro mês | sem evento de fim |
|---|---|---|---|---|---|
| renovacao_desligada | 16.145 | 16.145 | 0 | 0 | 0 |
| falha_pagamento | 1.321 | 1.321 | 0 | 0 | 0 |
| chargeback | 292 | 292 | 0 | 0 | 0 |
| reembolso | 72 | 72 | 0 | 0 | 0 |
| total | 17.830 | 17.830 | 0 | 0 | 0 |

- Diferença em dias (evento − `data_fim`) nas que têm evento: mediana 0, mínimo 0, máximo 0.
- Soma conferida: 17.830 = 17.830 ✔.
- As divergências são só descritas; nada foi corrigido. `data_fim` de `assinaturas.csv` é a fonte da série.

## 5. Alertas

- `assinaturas.csv` é um retrato de 01/10/2026: `inicio`, `data_fim` e `motivo_fim` servem para o histórico, mas `plano_atual` e `canal_cobranca` são os valores de hoje. Cuidado ao cruzar o churn com plano e canal (B3).
- `data_fim` mais antigo: 07/07/2024; o log de eventos começa em 01/07/2024.

## 6. Decisões 31 e 32 (gravadas no `decisoes.md` em 09/11/2026)

| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |
|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|
| 31 | 09/11/2026 | assinaturas.csv | definição do churn mensal | calcular a série de `inicio`/`data_fim` de `assinaturas.csv`, sem as contas de cortesia/teste; toda `data_fim` conta como perda (renovação desligada, falha de pagamento, chargeback, reembolso) | reproduz os números do case (8.540 ativos em jan/2025; abril/2026 = 1.154 sobre 14.237) | 32.643 → 32.583 assinaturas; 21 meses; 15.879 perdas |
| 32 | 09/11/2026 | eventos_assinatura.csv | conferir se `data_fim` de `assinaturas.csv` concorda com o evento de fim (17.830 encerradas desde 01/07/2024) | manter `data_fim` como fonte da série; eventos só para conferir (nada a corrigir) | divergência medida na seção 4: mesmo dia 17.830, mesmo mês 0, outro mês 0, sem evento 0 de 17.830 | 0 linhas alteradas |

---
Conferência: brutos inalterados.