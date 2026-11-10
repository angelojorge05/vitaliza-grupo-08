# Padronização e completude do onboarding (relatório final)

Base de saída: `dados/processados/base_conta_onboarding.csv` (fora do GitHub, pelo `.gitignore`). Refaz-se com os scripts abaixo, nesta ordem.
Nada em `dados/brutos/` foi alterado (SHA-256 igual antes e depois em cada script).

| Passo | Script | Resultado | Linhas |
|---|---|---|---|
| 1. Diagnóstico | `src/diagnostico_onboarding.py` | `saidas/diagnostico_onboarding.md` | 63.929 |
| 2. Padronização | `src/padronizar_onboarding.py` | `dados/processados/onboarding_padronizado.csv` | 63.929 → 63.929 |
| 3. Marcas de completude | `src/marcas_completude_onboarding.py` | `saidas/completude_marcas_onboarding.md` | 63.929 → 63.929 |
| 4. Base por conta | `src/base_conta_onboarding.py` | `dados/processados/base_conta_onboarding.csv` | 64.948 → 64.948 |
| 4b. Completude de usuarios | `src/completude_usuarios.py` | `saidas/completude_usuarios.md` | 64.948 |

## O que o diagnóstico encontrou
- `nivel`, `objetivo_texto` e `como_conheceu`: sem espaços nas pontas nem variação de caixa. `nivel` só tem `iniciante`, `intermediario` e `avancado`.
- `respondido_em`: um único formato (`AAAA-MM-DD`), de 01/09/2020 a 30/09/2026, nenhuma data depois do corte.
- `dias_por_semana`: 23 formas para os mesmos números.
- 0 `user_id` duplicado no onboarding e em `usuarios.csv`; nenhum `user_id` do onboarding fora de `usuarios.csv`; 1.019 contas sem onboarding.

## Padronização
- `dias_por_semana_num` (1 a 7): 56.644 linhas (88,60%). Distribuição: 1 → 4.502, 2 → 12.577, 3 → 17.161, 4 → 12.446, 5 → 6.179, 6 → 2.204, 7 → 1.575.
- "todos": 917 linhas **sem número** (decisão do usuário). Vazios: 6.368. Soma: 63.929.
- Colunas originais mantidas ao lado das novas.

## Completude final do onboarding
Nenhum vazio foi preenchido, então a completude é a mesma antes e depois das marcas.

| Medida | Valor |
|---|---:|
| Células preenchidas (7 colunas) | 95,32% |
| Só as 5 colunas não opcionais | 96,60% |
| Linhas sem nenhum vazio | 45.477 (71,14%) |
| Linhas sem vazio nas não opcionais | 53.521 (83,72%) |
| `dias_por_semana` com número | 56.644 (88,60%) |

Marcas: `nivel_nao_informado` 4.513; `dias_por_semana_nao_informado` 6.368; `objetivo_sem_resposta` 6.789; `como_conheceu_sem_resposta` 5.776.

## Base de uma linha por conta
- `usuarios.csv` (esquerda) + onboarding padronizado, `validate="one_to_one"`: **64.948 linhas antes e depois**, um `user_id` por linha, 0 duplicados.
- 63.929 contas com questionário e 1.019 com `sem_questionario = True`.
- 60 contas de teste marcadas em `flag_conta_teste` (mantidas).
- Aviso: nas 1.019 contas sem questionário, as quatro marcas de completude (`nivel_nao_informado` etc.) ficam **em branco**, e não `False`, porque a conta não tem linha no onboarding. Use `sem_questionario` para separá-las.

## Completude de `usuarios.csv` (64.948 contas)
| Coluna | Vazios | % |
|---|---:|---:|
| `data_nascimento` | 3.301 | 5,1% |
| `sexo` | 3.142 | 4,8% |
| `cep_prefixo` | 1.894 | 2,9% |
| demais 9 colunas | 0 | 0,0% |

Células preenchidas: 98,9%. Contas sem vazio em nenhuma das 12 colunas: 56.968 (87,7%).
O dicionário não marca nenhuma coluna de `usuarios.csv` como opcional (só `relogio_conectado` admite ausência, "se houver", e ali ela vem escrita como `nenhum`, não como vazio).

## Duplicatas
- Linhas: nenhuma duplicada por `user_id` nem por linha inteira; a junção não multiplicou nada.
- **959 e-mails** aparecem em duas contas, diferindo só por maiúsculas e minúsculas (1.918 contas; 472 têm assinatura; nenhuma é de teste). Em todos os 959 pares, nascimento, sexo e cidade coincidem. Provável pessoa em duas contas.

## Propostas não aplicadas (aguardam decisão do usuário)
| # | Arquivo | Problema | Decisão proposta | Motivo | Efeito na contagem |
|---|---|---|---|---|---|
| a definir | usuarios.csv | 959 e-mails em 2 contas cada (diferem só pela caixa) | marcar (`flag_email_repetido`); não juntar nem remover | cada `user_id` tem assinaturas, treinos e onboarding próprios; juntar contas exige uma regra que o dicionário não dá | 64.948 → 64.948; 1.918 marcadas |
| a definir | usuarios.csv | `data_nascimento` vazia (3.301), `sexo` vazio (3.142), `cep_prefixo` vazio (1.894) | marcar (`<coluna>_nao_informada`); manter vazio (a data de nascimento vazia continua vazia, como já decidido para os pagantes) | o dicionário não diz se podem ficar em branco; não há valor certo para corrigir | 64.948 → 64.948; 3.301, 3.142 e 1.894 marcadas |

## Pontos a registrar
- O dicionário descreve `nivel` só como "nível autodeclarado": os três valores vêm dos dados, sem lista oficial.
- A decisão 17 (colega) trata `dias_por_semana` só na base de pagantes de 30/06; as decisões 18 e 19 estendem o critério a todo o arquivo e tratam o "todos".
- As colunas de `usuarios.csv` na base por conta estão como no bruto (sexo, sistema e cidade com as grafias originais); a padronização dessas colunas já feita nas decisões 2 a 4 vale para o recorte de pagantes.
