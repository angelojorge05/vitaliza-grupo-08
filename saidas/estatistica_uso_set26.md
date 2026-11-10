# Estatística descritiva do uso em set/2026 (`uso_mensal.csv`, `mes = 2026-09`)

Gerado por `src/estatistica_uso_set26.py`. Só leitura (SHA-256 `844db26847fb785a…` conferido antes e depois). Nada foi alterado.

## 1. Linhas e contas

| passo | linhas | observação |
|---|---|---|
| uso_mensal.csv inteiro | 591.662 | 21 meses |
| só `mes = 2026-09` | 56.565 | 56.565 `user_id` únicos |
| contas de teste com linha em set/2026 | 0 | 60 contas de teste no total |
| sem contas de teste | 56.565 | 56.565 `user_id` únicos |

- Com e sem contas de teste: média 82,6 min contra 82,6 min (diferença nula: nenhuma conta de teste tem linha em `uso_mensal.csv`).
- Um `user_id` por linha: ✔.

## 2. Minutos: medidas de centro e dispersão

| versão | contas | média | mediana | moda | dp (n−1) | dp (n) | CV (dp n−1 ÷ média) |
|---|---|---|---|---|---|---|---|
| todas as contas (arquivo como está) | 56.565 | 82,6 | 0,0 | 0 (40.880 contas) | 221,3 | 221,3 | 2,68 |
| só minutos > 0 | 15.685 | 298,0 | 173,0 | 39 (131 contas) | 335,2 | 335,2 | 1,12 |

**n ou n−1?** Usei **n−1** (desvio amostral). Os 56 mil registros de set/2026 são todas as contas que têm linha no mês, ou seja, a população daquele mês; mas o que queremos descrever é o comportamento de uso que gera esses números (e comparar com outros meses), e nesse caso a população do mês é só uma amostra desse comportamento. Com 56.565 linhas a diferença é desprezível: dp (n−1) 221,258 contra dp (n) 221,256.

## 3. Proporção de contas com zero

| grupo | contas | % |
|---|---|---|
| minutos = 0 | 40.880 | 72,3% |
| minutos > 0 | 15.685 | 27,7% |
| minutos < 0 | 0 | 0,0% |
| total | 56.565 | 100,0% |

Conferência: 40.880 + 15.685 + 0 = 56.565 = linhas 56.565 ✔.

## 4. Quartis e máximo das duas versões

| versão | mínimo | Q1 | mediana | Q3 | máximo |
|---|---|---|---|---|---|
| todas as contas | 0 | 0,0 | 0,0 | 40,0 | 4.294 |
| só minutos > 0 | 15 | 71,0 | 173,0 | 408,0 | 4.294 |

## 5. Qual medida descreve a conta típica

Em set/2026, 72,3% das contas têm zero minuto, então a média (82,6 min) é puxada para baixo pelos zeros e a mediana e a moda são 0, o que descreve a conta típica do arquivo inteiro (que não treinou) mas não diz nada de quem treina. Para quem treinou, a mediana (173,0 min) é a medida mais honesta: a média (298,0 min) fica acima porque a cauda à direita (máximo 4.294 min) a puxa, e o CV de 1,12 mostra dispersão grande.

Nota: em 2026 o mês sem treino é uma linha com zero, e em 2025 era linha ausente (ver `temporalidade_uso_mensal.md`); a média sobre o arquivo só é comparável com 2025 se for calculada só para `minutos > 0`.

---
Conferência: bruto inalterado.