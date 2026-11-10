# Consistência de `tipo` em atividades.parquet

Gerado por `src/consistencia_atividades.py`. Só leitura: `atividades.parquet` com SHA-256 `b5269feac894938c…` conferido antes e depois. Nada foi aplicado.

## 1. Valores de `tipo`

| tipo | linhas |
|---|---|
| corrida | 223.818 |
| run | 162.108 |
| funcional | 145.476 |
| caminhada | 118.024 |
| yoga | 113.849 |
| forca | 112.704 |
| hiit | 109.934 |
| walk | 88.509 |
| strength | 85.548 |
| pedal | 53.740 |
| ride | 40.765 |

- Soma das contagens: **1.254.475** = total 1.254.475 = dicionário 1.254.475 ✔. Valores nulos: 0.
- Valores distintos: **11**.
- Maiúsculas, acentos e espaços: 0 valor(es) diferem da forma normalizada (minúsculas, sem acento, sem espaços nas pontas); 0 linhas com espaço nas pontas; 0 grupos que viram o mesmo valor depois de normalizar. Não há variação desse tipo.
- O dicionário só diz "tipo de treino", sem lista de valores; o mapa abaixo vem dos dados.

## 2. Tipo × origem

| tipo | app | apple_health | garmin | total |
|---|---|---|---|---|
| caminhada | 55.623 | 27.131 | 35.270 | 118.024 |
| corrida | 110.059 | 50.977 | 62.782 | 223.818 |
| forca | 53.833 | 25.732 | 33.139 | 112.704 |
| funcional | 69.293 | 33.555 | 42.628 | 145.476 |
| hiit | 109.934 | 0 | 0 | 109.934 |
| pedal | 26.072 | 12.690 | 14.978 | 53.740 |
| ride | 40.765 | 0 | 0 | 40.765 |
| run | 162.108 | 0 | 0 | 162.108 |
| strength | 85.548 | 0 | 0 | 85.548 |
| walk | 88.509 | 0 | 0 | 88.509 |
| yoga | 79.962 | 14.730 | 19.157 | 113.849 |

Nomes que aparecem em **uma só origem**: `hiit`, `ride`, `run`, `strength`, `walk`.
Origem de cada um: `hiit` → app; `ride` → app; `run` → app; `strength` → app; `walk` → app.

## 3. Mapa de padronização proposto (não aplicado)

| valor atual | valor padrão | linhas afetadas | onde aparece |
|---|---|---|---|
| run | corrida | 162.108 | só em app |
| walk | caminhada | 88.509 | só em app |
| ride | pedal | 40.765 | só em app |
| strength | forca | 85.548 | só em app |

Critério: o mesmo treino escrito em inglês e em português; o português é a forma majoritária e a que o dicionário usa em `atividades_ar_livre` (corrida, caminhada e pedal). Os destinos já existem nos dados: sim.

Valores mantidos como estão: `corrida`, `funcional`, `caminhada`, `yoga`, `forca`, `hiit`, `pedal`.
`hiit` também aparece só no `app`, mas não tem par em português nos dados (é a sigla usada nas duas línguas); por isso não entra no mapa.

## 4. Efeito do mapa

- Linhas afetadas: **376.930** (30.0% de 1.254.475).
- Soma das linhas por troca do mapa: **376.930** = linhas afetadas ✔.
- Tipos distintos: **11 → 7**. Linhas totais: 1.254.475 → 1.254.475 (nenhuma removida).

## 5. Decisão proposta (formato do `decisoes.md`, não gravada)

| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |
|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|
| — | 09/11/2026 | atividades.parquet | `tipo` em dois idiomas: 376.930 linhas (30%) com nome em inglês (run→corrida, walk→caminhada, ride→pedal, strength→forca), só na origem app | corrigir na cópia tratada: aplicar o mapa e deixar o bruto intacto | mesma categoria escrita de dois jeitos; contar só `corrida` deixaria de fora as linhas `run` | 376.930 linhas renomeadas; 11 → 7 tipos; 0 removidas |

Nota: isto reproduz a decisão 10 já em vigor (`src/preparar_atividades.py`); o resultado só serve de conferência independente.

---
Conferência: 1.254.475 linhas lidas, nenhuma alterada; `atividades.parquet` inalterado.