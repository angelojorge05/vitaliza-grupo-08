# Relatório exploratório · Vitaliza (corte 30/09/2026)

Fechamento do `prompts/00_analise_exploratoria_geral.md`. Reúne os blocos já gravados em `saidas/`; nenhum dado foi recalculado aqui. Regras seguidas em todos os blocos: `dados/brutos/` só leitura (SHA-256 conferido antes e depois), corte em 30/09/2026, horários UTC (`Z`) convertidos para Brasília, contas de teste (`@vitaliza.com.br`) fora das contas ou mostradas à parte.

## 1. Uma linha por bloco

| Bloco | O que mediu | Número principal | Arquivo |
|---|---|---|---|
| A1 · Completude | vazios por coluna do `onboarding.csv` (63.929 linhas, 1 por conta) | `dias_por_semana` 10,0% e `nivel` 7,1% vazios em campos **não opcionais**; `objetivo_texto` 8,6% (10,6% contando o traço `-`) | `completude_onboarding.md` |
| A2 · Validade | distância e duração impossíveis em `atividades.parquet` | 1.254.475 treinos; 679.640 com distância (54,2%); **951 acima de 200 km** (máx. 10.012,75 km); **3.649 com duração zero**; 7.455 com `gps_ok` falso e distância | `validade_atividades.md`, `limpeza_outliers_atividades.md` |
| A3 · Consistência | grafias de `tipo` e cruzamento com a origem | 11 valores → 7; **376.930 linhas (30,0%)** em inglês (`run`, `walk`, `ride`, `strength`), todas do `app` | `consistencia_atividades.md` |
| A4 · Unicidade | treinos em dobro app × relógio, com o fuso medido | garmin **+3 h** (UTC), apple_health 0 h; **9.383 pares** com a correção (4.184 sem ela); distância igual em 100% | `unicidade_atividades.md` |
| A5 · Temporalidade | registro do mês sem treino em `uso_mensal.csv` | 2025: mês sem treino = linha ausente (0 zeros); 2026: **69,1% das linhas são zero**; média só com `minutos > 0` estável (282,2 → 283,7 min) | `temporalidade_uso_mensal.md` |
| B · Granularidade | uma linha por conta com treinos | 64.948 contas → 64.948 linhas; **36.538 com treino**; 9.365 duplicatas marcadas (−0,75% dos treinos) | `granularidade_contas_treinos.md` |
| C · Descritiva set/2026 | minutos por conta no mês | **72,3% com zero**; mediana 173 min e média 298,0 min entre quem treinou (CV 1,12) | `estatistica_uso_set26.md` |
| D · Distribuição e extremos | distância por classes de 5 km, IQR e z | **pulado nesta rodada** (decisão do usuário). Resultado anterior, sobre o bruto: Q1 4,58 · mediana 6,47 · Q3 9,58 km; 81.775 acima do IQR e 956 com \|z\| > 3 | `distribuicao_distancias.md` (antigo) |
| E · Correlação e 3ª variável | r de `sessoes_app` × `minutos` controlando `atividades` | **pulado e não feito no formato do prompt.** O arquivo `terceira_variavel.md` testa outra coisa (churn × plano e tempo de casa), não esta correlação | — |

Fora do prompt 00, mas usado como referência: o churn mensal reconstruído reproduz o case (abril/2026 = 1.154 ÷ 14.237 = 8,1%; 14.753 ativos em 30/09), em `churn_mensal.md`.

## 2. Decisões

Todas as decisões dos blocos acima já foram aprovadas e estão gravadas no `decisoes.md`:

| # | Bloco | Decisão (resumo) | Efeito |
|---|---|---|---|
| 7, 8, 18 a 21 | A1 | marcar vazios e o traço como "não informado"/"sem resposta"; padronizar `dias_por_semana` em `dias_por_semana_num` | 63.929 → 63.929 linhas |
| 9, 23 a 27 | A2 | remover duração ≤ 0; anular distância > 200 km e com `gps_ok` falso; marcar IQR | 1.245.092 → 1.241.461 na cópia tratada |
| 10 | A3 | `tipo` canônico na cópia tratada | 376.930 renomeadas; 11 → 7 |
| 11 | A4 | remover o lado `app` de cada par na cópia tratada | −9.383 |
| 28 a 30 | B | uma linha por conta; corte com fuso corrigido; duplicatas só marcadas nesta base | 64.948 linhas |

Propostas ainda **não** gravadas (aguardam o grupo):

| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |
|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|
| — | 10/11/2026 | usuarios.csv | 959 e-mails repetidos por caixa (1.918 contas, 472 com assinatura) | marcar `flag_email_repetido`, sem juntar nem remover | não há regra no dicionário para dizer que duas contas são a mesma pessoa | 64.948 → 64.948; 1.918 marcadas |
| — | 10/11/2026 | usuarios.csv | vazios em `data_nascimento` (3.301), `sexo` (3.142) e `cep_prefixo` (1.894) | marcar "não informado", mantendo o vazio | não há valor certo para preencher | 64.948 → 64.948 |
| — | 10/11/2026 | uso_mensal.csv | mês sem treino é linha ausente em 2025 e zero em 2026 | marcar `linha_zero`; comparar anos só com `minutos > 0` | a média do arquivo não é comparável entre anos | 591.662 → 591.662; 303.735 marcadas |

## 3. Perguntas em aberto para o grupo

1. **E-mails repetidos:** duas contas com o mesmo e-mail são a mesma pessoa? Isso muda o churn por pessoa e a segmentação.
2. **Completude na segmentação:** o usuário pediu K-means só com contas completas. Entre os 14.753 ativos, 11.032 ficam (74,8%) e 3.721 saem. Quem não preenche o questionário se comporta diferente? (será medido antes de agrupar)
3. **`cancelamento_web`** é desligamento da renovação? (decisão 15: o resultado não muda, mas o dicionário não diz)
4. **Mensal fora do ciclo de 30 dias:** cerca de 8% dos mensais que saem têm `data_fim` fora dos múltiplos de 30 dias desde o início. Há pausa ou troca de ciclo? O dicionário não cita pausa.
5. **`hiit` só no `app`:** os relógios não registram HIIT, ou o app grava com outro nome? O dicionário não diz.
6. **Blocos D e E:** refazer sobre a base tratada (decisões 23 a 25) antes do modelo? O E, no formato do prompt, ainda não existe.

## 4. Achado de dados × hipótese

**Achados (medidos nos dados):**
- O garmin grava o início em UTC (+3 h): 5.199 de 5.223 candidatos caem a 5 min de +3,000 h; o apple_health está em Brasília.
- 30% dos treinos têm o `tipo` em inglês, todos do `app`.
- 9.383 treinos chegaram em dobro (app × relógio), com a mesma distância nos dois lados.
- 951 distâncias acima de 200 km e 3.649 durações zero são impossíveis.
- Em 2026 o mês sem treino passou a ser gravado como zero; em 2025 a linha não existe.
- `data_fim` de `assinaturas.csv` e o evento de fim caem no mesmo dia nas 17.830 encerradas desde 01/07/2024.
- Nenhuma conta de teste aparece em `uso_mensal.csv` nem em `atividades.parquet`.
- Nos cortes de treino, quem está com a renovação desligada sai em 60 dias 32,9% das vezes, contra 8,4% com ela ligada; mensal 20,8% contra anual 5,8%.

**Hipóteses (cruzamento aponta suspeitos, não prova causa):**
- A subida do churn em 2026 tem relação com o reajuste do mensal em 01/03 (o pico é abril, 8,1%).
- No anual, o uso cai meses antes da saída (mediana de treinos 9 contra 42 de quem ficou, em `terceira_variavel.md`).
- A campanha de 10/08 reduziu a saída: o experimento nunca foi analisado.
- Quem não preenche o questionário de entrada tem um perfil de uso diferente.
