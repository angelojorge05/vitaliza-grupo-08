# Análise 11 · Situação da renovação em 31/07/2026 (vazamento de dados)

Código: `src/analise_11_vazamento.py`. Tabela por conta: `dados/processados/situacao_renovacao_31jul.csv` (fora do GitHub).
Arquivos lidos (só leitura): `assinaturas.csv`, `usuarios.csv`, `eventos_assinatura.csv`.

## Pergunta
Entre os assinantes ativos em 01/10 com a renovação automática desligada, qual era a situação deles em 31/07/2026? Quantos o retrato de 01/10 classificaria errado?

## Linhas depois de cada passo
| Passo | Linhas |
|---|---|
| assinaturas.csv | 32.643 |
| status_atual = ativa | 14.813 |
| renovacao_automatica = nao | 2.310 |
| sem contas de teste (60 e-mails @vitaliza.com.br) | **2.250** |
| eventos_assinatura.csv | 275.565 |
| eventos das 2.250 contas (todas têm evento) | 9.418 |
| eventos até 31/07/2026 23:59:59 (Brasília) | 7.888 |
| junção com a situação (esquerda) | 2.250, um `user_id` por linha |

## Resultado
| Situação em 31/07/2026 | Contas | % |
|---|---|---|
| Renovação desligada | 1.427 | 63,4% |
| Renovação ligada | 754 | 33,5% |
| Ainda não assinava | 69 | 3,1% |
| **Total** | **2.250** | 100% |

O retrato de 01/10 diz "desligada" para as 2.250 e acerta 1.427. **Erra 823 (36,6%)**: é o tamanho do vazamento.

Todos os números batem com o "Confira" do roteiro.

## Cortes úteis
- Por plano: as 1.427 desligadas são todas do plano **anual**. As 168 mensais estão em ligada (122) ou ainda não assinavam (46). Entre as 2.082 anuais: 1.427 desligadas, 632 ligadas e 23 que ainda não assinavam.
- Por canal (desligada / ligada / não assinava): app_store 433 / 281 / 22; google_play 553 / 244 / 20; web_cartao 326 / 158 / 17; web_pix 115 / 71 / 10.
- 171 contas começaram antes de 01/07/2024 e não têm evento de início: 92 estavam desligadas e 79 ligadas em 31/07.

## Regras aplicadas
- **Fuso:** `data_hora` com `Z` é UTC e foi convertida para Brasília. O valor sem fuso (89.242 eventos) já está em Brasília. São 186.323 eventos com `Z`. A conversão muda o dia de 21.951 eventos em toda a base.
- **Último evento vale:** 223 contas têm mais de um desligamento e 16 têm três ou mais. A situação vem do último evento entre `renovacao_automatica_desligada` e `renovacao_automatica_religada` até 31/07.
- **Sem evento de renovação até 31/07:** renovação ligada (vale para quem começou antes de 01/07/2024).
- **Ainda não assinava:** `inicio` depois de 31/07/2026.
- **`cancelamento_web`:** testei as duas versões (sem e com `cancelamento_web` como desligamento). O resultado é idêntico (1.427, 754 e 69). O tipo não altera nenhuma classificação, e a versão principal não o conta.

## Conferência à mão (3 contas, no `eventos_assinatura.csv`)
| Conta | Eventos até 31/07 | Esperado | Resultado |
|---|---|---|---|
| u_00130058 | desligada 22/09/2025, religada 18/12/2025, desligada 14/06/2026 (3 desligamentos no total) | desligada | desligada |
| u_0173254b (início 03/05/2023, sem evento de início) | desligada 21/12/2024, religada 23/04/2025, depois só renovações | ligada | ligada |
| u_018e2889 (início 05/09/2026) | nenhum | ainda não assinava | ainda não assinava |

## Ressalvas
- O dicionário em PDF não foi lido; a regra de fuso vem do `contexto_case.md`.
- Não comparei o `inicio` do retrato com o evento `assinatura_iniciada` conta a conta. O `inicio` do retrato é a base da classificação "ainda não assinava".
