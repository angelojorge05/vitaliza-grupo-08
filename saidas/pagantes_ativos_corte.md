# Pagantes ativos no corte (30/09/2026)

**Total: 14.753**

O retrato bruto de `assinaturas.csv` tem 14.813 ativas, mas inclui as 60 contas de teste.

## Filtros

| Etapa | Linhas |
|---|---:|
| assinaturas.csv | 32.643 |
| status_atual = ativa (inclui testes) | 14.813 |
| usuarios.csv | 64.948 |
| junção ativas x usuarios (esquerda) | 14.813 |
| ativas sem contas de teste (pagantes no corte) | 14.753 |

## Por plano

| Plano | n | % |
|---|---:|---:|
| anual | 8.478 | 57.5 |
| mensal | 6.275 | 42.5 |

## Por canal de cobrança

| Canal | n | % |
|---|---:|---:|
| app_store | 5.395 | 36.6 |
| google_play | 4.964 | 33.6 |
| web_cartao | 2.994 | 20.3 |
| web_pix | 1.400 | 9.5 |

## Qualidade das datas em `usuarios.csv`

Pagantes ativos = assinatura `ativa` no corte, sem contas de teste (14.753). Corte em 30/09/2026.
Nenhuma linha foi alterada ou removida: os problemas ficam só contados e marcados.

| Situação | Base toda (64.948) | Pagantes ativos (14.753) |
|---|---:|---:|
| **Sem data de nascimento (vazia)** | **3.301 (5,1%)** | **764 (5,2%)** |
| Nascimento depois do corte | 194 | 47 |
| Nascimento antes de 1920 (todos 01/01/1900) | 412 | 86 |
| Nascimento inválido (as duas linhas acima) | 606 (0,9%) | 133 (0,9%) |
| Nascimento inválido ou vazio | 3.907 (6,0%) | 897 (6,1%) |
| Cadastro depois do corte | 119 | 0 |

- Os 47 pagantes com nascimento depois do corte também têm o cadastro anterior ao nascimento: é erro de digitação.
- As 119 contas com cadastro depois do corte (de 01/10/2026 a 04/04/2027) não têm assinatura, então não afetam os 14.753.
- Nenhuma conta de teste tem data inválida.
