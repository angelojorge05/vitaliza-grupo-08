# Completude do onboarding.csv (Análise 2, conferência independente)

Código: `src/completude_onboarding.py`. Leitura em texto puro (`dtype=str`, `keep_default_na=False`). Nada em `dados/brutos/` foi alterado (SHA-256 igual antes e depois).

## Linhas

- Linhas: **63.929** (dicionário: 63.929).
- `user_id` únicos: **63.929**; linhas com `user_id` repetido: 0.

## Vazios por coluna (da mais vazia para a menos vazia)

| Coluna | Nulos | Só espaço | Vazios | % das linhas | Traço `-` | Opcional (dicionário) |
|---|---:|---:|---:|---:|---:|---|
| `dias_por_semana` | 6.368 | 0 | 6.368 | 10,0% | — | não |
| `objetivo_texto` | 5.467 | 0 | 5.467 | 8,6% | 1.322 | sim |
| `como_conheceu` | 4.586 | 0 | 4.586 | 7,2% | 1.190 | sim |
| `nivel` | 4.513 | 0 | 4.513 | 7,1% | — | não |
| `onboarding_id` | 0 | 0 | 0 | 0,0% | — | não |
| `respondido_em` | 0 | 0 | 0 | 0,0% | — | não |
| `user_id` | 0 | 0 | 0 | 0,0% | — | não |

Soma conferida: em cada coluna, nulos + só espaço = vazios, e o total de linhas (63.929) é o mesmo antes e depois.

## Traço `-` como ausência (colunas opcionais)

| Coluna | Vazios | Traço | Ausentes sem o traço | Ausentes com o traço |
|---|---:|---:|---:|---:|
| `objetivo_texto` | 5.467 | 1.322 | 5.467 (8,6%) | 6.789 (10,6%) |
| `como_conheceu` | 4.586 | 1.190 | 4.586 (7,2%) | 5.776 (9,0%) |

## O que o dicionário diz (seção 10)

- A tabela de colunas marca `objetivo_texto` e `como_conheceu` como opcionais. Não são opcionais: `onboarding_id`, `user_id`, `respondido_em`, `nivel` e `dias_por_semana`.
- **Ressalva:** o texto da seção diz só que "o objetivo é opcional". Por decisão do usuário (09/11/2026), `como_conheceu` foi tratada como opcional, como na tabela.
- O dicionário não diz que `nivel` e `dias_por_semana` possam ficar sem resposta; por isso o vazio ali é problema.

## Conferência com o colega (decisões 7 e 8)

- `nivel` vazios: 4.513 (colega: 4.513) → confere
- `dias_por_semana` vazios: 6.368 (colega: 6.368) → confere
- `objetivo_texto` traço: 1.322 (colega: 1.322) → confere
- `como_conheceu` traço: 1.190 (colega: 1.190) → confere

## Decisões propostas (não aplicadas; formato do `decisoes.md`)

| # | Data | Arquivo | Problema | Decisão | Motivo | Efeito na contagem |
|---|---|---|---|---|---|---|
| a definir | 09/11/2026 | onboarding.csv | Vazios em `dias_por_semana` (campo não opcional): 6.368 (10,0%) | marcar (`dias_por_semana_nao_informado`, mantendo o valor original vazio) | o dicionário não marca a coluna como opcional, então o vazio é lacuna real; não há valor certo para corrigir, e remover perderia contas com o resto da resposta | 63.929 → 63.929 (0 removidas; 6.368 marcadas) |
| a definir | 09/11/2026 | onboarding.csv | Vazios em `nivel` (campo não opcional): 4.513 (7,1%) | marcar (`nivel_nao_informado`, mantendo o valor original vazio) | o dicionário não marca a coluna como opcional, então o vazio é lacuna real; não há valor certo para corrigir, e remover perderia contas com o resto da resposta | 63.929 → 63.929 (0 removidas; 4.513 marcadas) |
