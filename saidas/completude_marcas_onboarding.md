# Completude do onboarding: marcas (Passo 3)

Código: `src/marcas_completude_onboarding.py`. Nenhum vazio foi preenchido: as marcas só sinalizam a lacuna.

## Marcas criadas

| Marca | Contas marcadas | % das linhas | Regra |
|---|---:|---:|---|
| `nivel_nao_informado` | 4.513 | 7,06% | `nivel` vazio |
| `dias_por_semana_nao_informado` | 6.368 | 9,96% | `dias_por_semana` vazio |
| `objetivo_sem_resposta` | 6.789 | 10,62% | vazio (5.467) ou traço `-` (1.322) |
| `como_conheceu_sem_resposta` | 5.776 | 9,04% | vazio (4.586) ou traço `-` (1.190) |

## Completude (antes = depois, pois nada foi preenchido)

| Medida | Valor |
|---|---:|
| Células preenchidas (7 colunas) | 95,32% |
| Só as 5 colunas não opcionais | 96,60% |
| Linhas sem nenhum vazio | 45.477 (71,14%) |
| Linhas sem vazio nas não opcionais | 53.521 (83,72%) |

## Efeito da padronização em `dias_por_semana`

- Com número de 1 a 7: **56.644** (88,60%); antes, só as respostas escritas só como `N` eram diretamente numéricas.
- Sem número: **7.285** (11,40%) = 6.368 vazios + 917 `todos`.
- Linhas: 63.929 antes e depois, um `user_id` por linha.
