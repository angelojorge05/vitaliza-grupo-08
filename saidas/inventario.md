# Inventário de dados/brutos/

Gerado em 29/10/2026 21:34 por `src/inventario.py`. Para gerar de novo: `.venv\Scripts\python src\inventario.py`.

Só leitura: nenhum arquivo bruto foi alterado (hash SHA-256 conferido antes e depois) e nenhuma limpeza foi feita. Referência: `docs/Vitaliza - Dicionário de dados.pdf`.

**Como ler**

- **Tipo (pandas):** o tipo que o pandas adivinharia sozinho ao ler o arquivo.
- **Conteúdo:** o que os valores parecem ser, lidos como texto. Datas mostram o formato.
- **Nulos:** célula sem valor (no CSV, lido como texto, quase sempre zero). **Vazios:** texto vazio ou só com espaços. **Marcadores:** textos como `null`, `NA`, `N/A`, `-`, `nan`, `none`, `?`.
- **Datas** são comparadas já em horário de Brasília: valores com `Z` (UTC) são convertidos antes da comparação com o corte de 30/09/2026.
- **Divergências** contrariam algo que o dicionário afirma. **Observações** são problemas de qualidade que o dicionário já avisa que existem (formatos, fusos, maiúsculas).

## Resumo

| Arquivo | Linhas | Dicionário | Colunas | Células faltantes | Divergências |
|---|---:|---:|---:|---:|---:|
| [usuarios.csv](#usuarioscsv) | 64.948 | 64.948 | 12 | 1,1% | 2 |
| [assinaturas.csv](#assinaturascsv) | 32.643 | 32.643 | 9 | 10,1% | 2 |
| [amizades.csv](#amizadescsv) | 113.480 | 113.480 | 3 | 0,0% | 1 |
| [campanha_ago26.csv](#campanha_ago26csv) | 14.120 | 14.120 | 9 | 16,8% | 0 |
| [eventos_assinatura.csv](#eventos_assinaturacsv) | 275.565 | 275.565 | 6 | 20,7% | 0 |
| [pagamentos.csv](#pagamentoscsv) | 165.548 | 165.548 | 7 | 0,0% | 0 |
| [uso_mensal.csv](#uso_mensalcsv) | 591.662 | 591.662 | 8 | 0,0% | 0 |
| [atividades.parquet](#atividadesparquet) | 1.254.475 | 1.254.475 | 11 | 22,9% | 1 |
| [onboarding.csv](#onboardingcsv) | 63.929 | 63.929 | 7 | 5,2% | 0 |
| [pesquisa_saida.csv](#pesquisa_saidacsv) | 643 | 643 | 5 | 5,7% | 0 |
| [feed_posts.csv](#feed_postscsv) | 119.309 | 119.309 | 5 | 0,0% | 1 |
| [tickets_suporte.csv](#tickets_suportecsv) | 4.422 | 4.422 | 8 | 4,3% | 1 |
| [heatmaps/heatmaps_2026-07-31.zip](#heatmaps) | 12.426 imagens | 12.426 | - | - | 0 |
| [heatmaps/heatmaps_2026-09-30.zip](#heatmaps) | 13.047 imagens | 13.047 | - | - | 0 |

## Divergências consolidadas

- **usuarios.csv**: `data_cadastro`: 119 linhas depois da data de corte (30/09/2026, já em horário de Brasília).
- **usuarios.csv**: `data_nascimento`: 194 linhas depois da data de corte (30/09/2026, já em horário de Brasília).
- **assinaturas.csv**: `plano_atual`: 1 valores fora da lista do dicionário, em 60 linhas: `cortesia` (60).
- **assinaturas.csv**: `canal_cobranca`: 1 valores fora da lista do dicionário, em 60 linhas: `interno` (60).
- **amizades.csv**: `desde`: 273 linhas depois da data de corte (30/09/2026, já em horário de Brasília).
- **atividades.parquet**: `inicio`: 34 linhas depois da data de corte (30/09/2026, já em horário de Brasília).
- **feed_posts.csv**: `data_hora`: 122 linhas depois da data de corte (30/09/2026, já em horário de Brasília).
- **tickets_suporte.csv**: `resolvido_em`: 41 linhas depois da data de corte (30/09/2026, já em horário de Brasília).

## usuarios.csv

- **Formato:** CSV, separador `,`, utf-8 · 7,9 MB
- **Uma linha por:** conta (dicionário)
- **Linhas:** 64.948 · dicionário: 64.948 · confere
- **Colunas:** 12 · dicionário: 12
- **Células faltantes** (nulo, vazio ou marcador): 8.337 de 779.376 (1,1%)
- **Linhas duplicadas por inteiro:** 0

| Coluna | Tipo (pandas) | Conteúdo | Nulos | Vazios | Marcadores | % faltante | Distintos | Faixa ou mais frequentes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `user_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 64.948 | `u_997536a0` (1); `u_22089975` (1); `u_25b2c840` (1) |
| `email` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 64.948 | `***@hotmail.com` (1); `***@gmail.com` (1); `***@hotmail.com` (1) |
| `data_cadastro` | str | data e hora 100,0% | 0 | 0 | 0 | 0,0% | 60.938 | 2020-09-01 12:00 a 2027-04-04 10:44 |
| `data_nascimento` | str | data 100,0% | 0 | 3.301 | 0 | 5,1% | 15.201 | 1900-01-01 a 2031-05-12 |
| `sexo` | str | texto 100,0% | 0 | 3.142 | 0 | 4,8% | 6 | `F` (19.330); `M` (17.646); `Fem` (6.657); `feminino` (6.520); `Masc` (5.838); `masculino` (5.815) |
| `cidade` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 36 | `São Paulo` (19.096); `Rio de Janeiro` (5.268); `Curitiba` (3.922) |
| `uf` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 11 | `SP` (31.994); `RJ` (7.513); `MG` (4.550); `PR` (3.922); `DF` (3.268); `RS` (3.267); `SC` (2.674); `GO` (1.950); `PE` (1.940); `CE` (1.939); `BA` (1.931) |
| `cep_prefixo` | float64 | inteiro 59,4% · número com zero à esquerda 40,6% | 0 | 1.894 | 0 | 2,9% | 242 | 10 a 918 |
| `canal_aquisicao` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 7 | `organico` (18.531); `influenciador` (14.067); `meta_ads` (11.939); `indicacao` (8.117); `google_ads` (6.801); `parceria_corporativa` (5.433); `interno` (60) |
| `sistema` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 5 | `android` (28.027); `ios` (20.854); `iOS` (7.463); `Android` (7.124); `IOS` (1.480) |
| `versao_app` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 6 | `5.4.1` (20.010); `5.4.0` (19.996); `5.3.2` (9.899); `5.3.0` (9.795); `5.1.0` (2.644); `4.9.8` (2.604) |
| `relogio_conectado` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 3 | `nenhum` (40.159); `garmin` (13.403); `apple_watch` (11.386) |

**Divergências em relação ao dicionário**

- `data_cadastro`: 119 linhas depois da data de corte (30/09/2026, já em horário de Brasília).
- `data_nascimento`: 194 linhas depois da data de corte (30/09/2026, já em horário de Brasília).

**Observações de qualidade** (não contrariam o dicionário, mas pedem tratamento)

- `cidade`: o mesmo valor aparece escrito de jeitos diferentes (maiúsculas ou acentos): `BELO HORIZONTE` / `Belo Horizonte` / `Belo horizonte`; `Brasilia` / `Brasília` / `brasilia`; `Florianopolis` / `Florianópolis`; `Floripa` / `floripa`; `RIO DE JANEIRO` / `Rio de Janeiro` / `Rio de janeiro` / `rio de janeiro`; `SAO PAULO` / `Sao Paulo` / `São Paulo` / `são paulo`.
- `cep_prefixo`: 25.583 números com zero à esquerda (manter como texto).
- `sistema`: o mesmo valor aparece escrito de jeitos diferentes (maiúsculas ou acentos): `Android` / `android`; `IOS` / `iOS` / `ios`.
- Contas de teste (`@vitaliza.com.br`, sem diferenciar maiúsculas): 60. Só contadas aqui; a regra do CLAUDE.md é excluí-las.

## assinaturas.csv

- **Formato:** CSV, separador `,`, utf-8 · 2,5 MB
- **Uma linha por:** assinatura (retrato de 01/10/2026) (dicionário)
- **Linhas:** 32.643 · dicionário: 32.643 · confere
- **Colunas:** 9 · dicionário: 9
- **Células faltantes** (nulo, vazio ou marcador): 29.626 de 293.787 (10,1%)
- **Linhas duplicadas por inteiro:** 0

| Coluna | Tipo (pandas) | Conteúdo | Nulos | Vazios | Marcadores | % faltante | Distintos | Faixa ou mais frequentes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `assinatura_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 32.643 | `s_000000` (1); `s_000001` (1); `s_000002` (1) |
| `user_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 32.643 | `u_f4d898b7` (1); `u_066eb85c` (1); `u_fec25b29` (1) |
| `plano_atual` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 3 | `mensal` (19.556); `anual` (13.027); `cortesia` (60) |
| `canal_cobranca` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 5 | `app_store` (11.170); `google_play` (10.948); `web_cartao` (7.087); `web_pix` (3.378); `interno` (60) |
| `inicio` | str | data 100,0% | 0 | 0 | 0 | 0,0% | 2.170 | 2020-09-08 a 2026-09-30 |
| `status_atual` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 3 | `expirada` (17.758); `ativa` (14.813); `reembolsada` (72) |
| `renovacao_automatica` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 2 | `nao` (20.140); `sim` (12.503) |
| `data_fim` | str | data 100,0% | 0 | 14.813 | 0 | 45,4% | 814 | 2024-07-07 a 2026-09-30 |
| `motivo_fim` | str | texto 100,0% | 0 | 14.813 | 0 | 45,4% | 4 | `renovacao_desligada` (16.145); `falha_pagamento` (1.321); `chargeback` (292); `reembolso` (72) |

**Divergências em relação ao dicionário**

- `plano_atual`: 1 valores fora da lista do dicionário, em 60 linhas: `cortesia` (60).
- `canal_cobranca`: 1 valores fora da lista do dicionário, em 60 linhas: `interno` (60).

**Observações de qualidade** (não contrariam o dicionário, mas pedem tratamento)

- Nenhuma.

## amizades.csv

- **Formato:** CSV, separador `,`, utf-8 · 3,7 MB
- **Uma linha por:** relação de seguir (dicionário)
- **Linhas:** 113.480 · dicionário: 113.480 · confere
- **Colunas:** 3 · dicionário: 3
- **Células faltantes** (nulo, vazio ou marcador): 0 de 340.440 (0,0%)
- **Linhas duplicadas por inteiro:** 0

| Coluna | Tipo (pandas) | Conteúdo | Nulos | Vazios | Marcadores | % faltante | Distintos | Faixa ou mais frequentes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `seguidor_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 50.455 | `u_28524e92` (13); `u_ea0416cb` (12); `u_6d49544e` (11) |
| `seguido_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 50.547 | `u_26ec2fcc` (13); `u_a24ac69e` (12); `u_8dcd8b08` (11) |
| `desde` | str | data 100,0% | 0 | 0 | 0 | 0,0% | 2.211 | 2020-09-05 a 2026-10-09 |

**Divergências em relação ao dicionário**

- `desde`: 273 linhas depois da data de corte (30/09/2026, já em horário de Brasília).

**Observações de qualidade** (não contrariam o dicionário, mas pedem tratamento)

- Nenhuma.

## campanha_ago26.csv

- **Formato:** CSV, separador `,`, utf-8 · 1,3 MB
- **Uma linha por:** assinante sorteado (dicionário)
- **Linhas:** 14.120 · dicionário: 14.120 · confere
- **Colunas:** 9 · dicionário: 9
- **Células faltantes** (nulo, vazio ou marcador): 21.385 de 127.080 (16,8%)
- **Linhas duplicadas por inteiro:** 0

| Coluna | Tipo (pandas) | Conteúdo | Nulos | Vazios | Marcadores | % faltante | Distintos | Faixa ou mais frequentes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `user_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 14.120 | `u_f4d898b7` (1); `u_411ca38a` (1); `u_56c52347` (1) |
| `grupo` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 4 | `controle` (3.579); `conteudo` (3.554); `desafio` (3.515); `cupom` (3.472) |
| `enviado_em` | str | data e hora 100,0% | 0 | 3.579 | 0 | 25,3% | 1 | 2026-08-10 10:00 a 2026-08-10 10:00 · `2026-08-10 10:00:00` (10.541) |
| `canal` | str | texto 100,0% | 0 | 3.579 | 0 | 25,3% | 1 | `push+email` (10.541) |
| `titulo_mensagem` | str | texto 100,0% | 0 | 3.579 | 0 | 25,3% | 3 | `Seu plano de treino pers…` (3.554); `Novo desafio de 6 semana…` (3.515); `Oferta para voltar a tre…` (3.472) |
| `oferta` | str | texto 100,0% | 0 | 10.648 | 0 | 75,4% | 2 | `1_mes_gratis` (2.052); `30pct_3_meses` (1.420) |
| `abriu_push` | bool | booleano 100,0% | 0 | 0 | 0 | 0,0% | 2 | `False` (10.808); `True` (3.312) |
| `abriu_email` | bool | booleano 100,0% | 0 | 0 | 0 | 0,0% | 2 | `False` (12.176); `True` (1.944) |
| `clicou` | bool | booleano 100,0% | 0 | 0 | 0 | 0,0% | 2 | `False` (12.516); `True` (1.604) |

**Divergências em relação ao dicionário**

- Nenhuma.

**Observações de qualidade** (não contrariam o dicionário, mas pedem tratamento)

- Nenhuma.

## eventos_assinatura.csv

- **Formato:** CSV, separador `,`, utf-8 · 17,7 MB
- **Uma linha por:** evento (dicionário)
- **Linhas:** 275.565 · dicionário: 275.565 · confere
- **Colunas:** 6 · dicionário: 6
- **Células faltantes** (nulo, vazio ou marcador): 342.367 de 1.653.390 (20,7%)
- **Linhas duplicadas por inteiro:** 0

| Coluna | Tipo (pandas) | Conteúdo | Nulos | Vazios | Marcadores | % faltante | Distintos | Faixa ou mais frequentes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `user_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 52.196 | `u_ca038b00` (31); `u_bb409a18` (30); `u_9bd788e5` (30) |
| `data_hora` | str | data e hora UTC (Z) 67,6% · data e hora 32,4% | 0 | 0 | 0 | 0,0% | 275.116 | 2024-07-01 06:11 a 2026-09-30 22:59 |
| `evento` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 11 | `renovacao` (132.606); `trial_iniciado` (46.996); `assinatura_iniciada` (27.383); `renovacao_automatica_des…` (26.923); `trial_expirado` (19.143); `assinatura_expirada` (17.830); `renovacao_automatica_rel…` (1.798); `periodo_carencia` (1.346); `cancelamento_web` (1.172); `chargeback` (296); `reembolso` (72) |
| `plano` | str | texto 100,0% | 0 | 72.873 | 0 | 26,4% | 2 | `mensal` (170.993); `anual` (31.699) |
| `canal_cobranca` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 4 | `google_play` (93.582); `app_store` (92.741); `web_cartao` (58.775); `web_pix` (30.467) |
| `detalhe` | str | texto 100,0% | 0 | 269.494 | 0 | 97,8% | 4 | `renovacao_desligada` (5.139); `falha_pagamento` (800); `chargeback` (109); `reembolso` (23) |

**Divergências em relação ao dicionário**

- Nenhuma.

**Observações de qualidade** (não contrariam o dicionário, mas pedem tratamento)

- `data_hora`: 2 formatos de data diferentes: `9999-99-99T99:99:99Z` (186.323), `9999-99-99 99:99:99` (89.242).
- `data_hora`: 186.323 valores em UTC (terminam em `Z`); os demais não indicam fuso.

## pagamentos.csv

- **Formato:** CSV, separador `,`, utf-8 · 11,6 MB
- **Uma linha por:** tentativa de cobrança (dicionário)
- **Linhas:** 165.548 · dicionário: 165.548 · confere
- **Colunas:** 7 · dicionário: 7
- **Células faltantes** (nulo, vazio ou marcador): 0 de 1.158.836 (0,0%)
- **Linhas duplicadas por inteiro:** 0

| Coluna | Tipo (pandas) | Conteúdo | Nulos | Vazios | Marcadores | % faltante | Distintos | Faixa ou mais frequentes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `pagamento_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 165.548 | `p_0000000` (1); `p_0000001` (1); `p_0000002` (1) |
| `user_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 31.782 | `u_9514dd66` (32); `u_b9797a55` (31); `u_1c3dfc30` (31) |
| `data_hora` | str | data e hora UTC (Z) 67,7% · data e hora 32,3% | 0 | 0 | 0 | 0,0% | 163.473 | 2024-07-02 06:14 a 2026-09-30 22:54 |
| `valor` | str | decimal 88,1% · texto 11,9% | 0 | 0 | 0 | 0,0% | 9 | -299.9 a 299.9 · `34.90` (85.508); `39.90` (44.632); `R$ 34,90` (17.746); `299.90` (13.732); `R$ 299,90` (1.852); `239.90` (1.558); `-39.90` (206); `-299.90` (162); `R$ 239,90` (152) |
| `metodo` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 4 | `app_store` (57.020); `google_play` (55.106); `cartao` (34.676); `pix_automatico` (18.746) |
| `status` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 4 | `aprovado` (161.930); `recusado` (3.250); `chargeback` (296); `estornado` (72) |
| `tentativa` | int64 | inteiro 100,0% | 0 | 0 | 0 | 0,0% | 2 | 1 a 2 · `1` (160.682); `2` (4.866) |

**Divergências em relação ao dicionário**

- Nenhuma.

**Observações de qualidade** (não contrariam o dicionário, mas pedem tratamento)

- `data_hora`: 2 formatos de data diferentes: `9999-99-99T99:99:99Z` (112.126), `9999-99-99 99:99:99` (53.422).
- `data_hora`: 112.126 valores em UTC (terminam em `Z`); os demais não indicam fuso.
- `valor`: mistura tipos (decimal 88,1% · texto 11,9%); exemplos do que não é número: `R$ 34,90`, `R$ 299,90`, `R$ 239,90`.

## uso_mensal.csv

- **Formato:** CSV, separador `,`, utf-8 · 19,1 MB
- **Uma linha por:** usuário e mês (dicionário)
- **Linhas:** 591.662 · dicionário: 591.662 · confere
- **Colunas:** 8 · dicionário: 8
- **Células faltantes** (nulo, vazio ou marcador): 0 de 4.733.296 (0,0%)
- **Linhas duplicadas por inteiro:** 0

| Coluna | Tipo (pandas) | Conteúdo | Nulos | Vazios | Marcadores | % faltante | Distintos | Faixa ou mais frequentes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `user_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 63.830 | `u_f4d898b7` (21); `u_56c52347` (21); `u_a0a5299f` (21) |
| `mes` | str | mês AAAA-MM 100,0% | 0 | 0 | 0 | 0,0% | 21 | 2025-01-01 a 2026-09-01 |
| `atividades` | int64 | inteiro 100,0% | 0 | 0 | 0 | 0,0% | 67 | 0 a 68 |
| `atividades_ar_livre` | int64 | inteiro 100,0% | 0 | 0 | 0 | 0,0% | 53 | 0 a 53 |
| `atividades_video` | int64 | inteiro 100,0% | 0 | 0 | 0 | 0,0% | 52 | 0 a 57 |
| `minutos` | int64 | inteiro 100,0% | 0 | 0 | 0 | 0,0% | 2.534 | 0 a 8228 |
| `dias_ativos` | int64 | inteiro 100,0% | 0 | 0 | 0 | 0,0% | 31 | 0 a 30 |
| `sessoes_app` | int64 | inteiro 100,0% | 0 | 0 | 0 | 0,0% | 135 | 0 a 153 |

**Divergências em relação ao dicionário**

- Nenhuma.

**Observações de qualidade** (não contrariam o dicionário, mas pedem tratamento)

- Nenhuma.

## atividades.parquet

- **Formato:** parquet · 19,1 MB
- **Uma linha por:** treino (dicionário)
- **Linhas:** 1.254.475 · dicionário: 1.254.475 · confere
- **Colunas:** 11 · dicionário: 11
- **Células faltantes** (nulo, vazio ou marcador): 3.162.450 de 13.799.225 (22,9%)
- **Linhas duplicadas por inteiro:** 0

| Coluna | Tipo (pandas) | Conteúdo | Nulos | Vazios | Marcadores | % faltante | Distintos | Faixa ou mais frequentes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `atividade_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 1.254.475 | `a_0201284` (1); `a_0494967` (1); `a_0541039` (1) |
| `user_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 36.551 | `u_fb37c43b` (476); `u_5e663e78` (376); `u_0e8e6152` (368) |
| `inicio` | str | data e hora 100,0% | 0 | 0 | 0 | 0,0% | 223.408 | 2026-01-01 05:00 a 2026-10-01 00:59 |
| `tipo` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 11 | `corrida` (223.818); `run` (162.108); `funcional` (145.476); `caminhada` (118.024); `yoga` (113.849); `forca` (112.704); `hiit` (109.934); `walk` (88.509); `strength` (85.548); `pedal` (53.740); `ride` (40.765) |
| `duracao_min` | float64 | decimal 100,0% | 0 | 0 | 0 | 0,0% | 3.289 | 0 a 543.9 |
| `distancia_km` | float64 | decimal 100,0% | 574.835 | 0 | 0 | 45,8% | 9.584 | 0 a 10012.8 |
| `ritmo_min_km` | float64 | decimal 100,0% | 582.290 | 0 | 0 | 46,4% | 1.007 | 1.8 a 13 |
| `fc_media` | float64 | decimal 100,0% | 764.987 | 0 | 0 | 61,0% | 133 | 61 a 195 |
| `origem` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 3 | `app` (881.706); `garmin` (207.954); `apple_health` (164.815) |
| `gps_ok` | bool | booleano 100,0% | 0 | 0 | 0 | 0,0% | 2 | `True` (1.239.696); `False` (14.779) |
| `treino_com` | str | texto 100,0% | 0 | 1.240.338 | 0 | 98,9% | 2.765 | `u_26ec2fcc` (59); `u_f3b52442` (49); `u_0e8e6152` (47) |

**Divergências em relação ao dicionário**

- `inicio`: 34 linhas depois da data de corte (30/09/2026, já em horário de Brasília).

**Observações de qualidade** (não contrariam o dicionário, mas pedem tratamento)

- Nenhuma.

## onboarding.csv

- **Formato:** CSV, separador `,`, utf-8 · 5,7 MB
- **Uma linha por:** conta (dicionário)
- **Linhas:** 63.929 · dicionário: 63.929 · confere
- **Colunas:** 7 · dicionário: 7
- **Células faltantes** (nulo, vazio ou marcador): 23.446 de 447.503 (5,2%)
- **Linhas duplicadas por inteiro:** 0

| Coluna | Tipo (pandas) | Conteúdo | Nulos | Vazios | Marcadores | % faltante | Distintos | Faixa ou mais frequentes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `onboarding_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 63.929 | `o_000000` (1); `o_000001` (1); `o_000002` (1) |
| `user_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 63.929 | `u_f4d898b7` (1); `u_066eb85c` (1); `u_fec25b29` (1) |
| `respondido_em` | str | data 100,0% | 0 | 0 | 0 | 0,0% | 2.177 | 2020-09-01 a 2026-09-30 |
| `objetivo_texto` | str | texto 100,0% | 0 | 5.467 | 1.322 | 10,6% | 17.188 | `nada` (1.426); `😂` (1.413); `.` (1.398) |
| `como_conheceu` | str | texto 100,0% | 0 | 4.586 | 1.190 | 9,0% | 570 | `vi no google` (3.520); `procurei app de corrida …` (3.204); `já conhecia` (2.842) |
| `nivel` | str | texto 100,0% | 0 | 4.513 | 0 | 7,1% | 3 | `intermediario` (25.631); `iniciante` (23.682); `avancado` (10.103) |
| `dias_por_semana` | str | inteiro 58,2% · texto 41,8% | 0 | 6.368 | 0 | 10,0% | 22 | 1 a 7 |

**Divergências em relação ao dicionário**

- Nenhuma.

**Observações de qualidade** (não contrariam o dicionário, mas pedem tratamento)

- `objetivo_texto`: 1.322 valores que parecem marcar ausência: `-` (1.322).
- `como_conheceu`: 1.190 valores que parecem marcar ausência: `-` (1.190).
- `dias_por_semana`: mistura tipos (inteiro 58,2% · texto 41,8%); exemplos do que não é número: `3 vezes`, `3x`, `2x`.

## pesquisa_saida.csv

- **Formato:** CSV, separador `,`, utf-8 · 42 KB
- **Uma linha por:** resposta (dicionário)
- **Linhas:** 643 · dicionário: 643 · confere
- **Colunas:** 5 · dicionário: 5
- **Células faltantes** (nulo, vazio ou marcador): 183 de 3.215 (5,7%)
- **Linhas duplicadas por inteiro:** 0

| Coluna | Tipo (pandas) | Conteúdo | Nulos | Vazios | Marcadores | % faltante | Distintos | Faixa ou mais frequentes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `resposta_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 643 | `q_00000` (1); `q_00001` (1); `q_00002` (1) |
| `user_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 641 | `u_84494960` (2); `u_615b71d0` (2); `u_e2e082a4` (1) |
| `respondido_em` | str | data 100,0% | 0 | 0 | 0 | 0,0% | 121 | 2026-06-01 a 2026-09-30 |
| `motivo_principal` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 6 | `preco` (264); `outro` (223); `nao_uso` (81); `outro_app` (34); `problema_tecnico` (27); `saude` (14) |
| `comentario` | str | texto 100,0% | 0 | 183 | 0 | 28,5% | 142 | `treinei pra prova e cons…` (28); `já fiz a prova, agora nã…` (27); `era só até a prova` (25) |

**Divergências em relação ao dicionário**

- Nenhuma.

**Observações de qualidade** (não contrariam o dicionário, mas pedem tratamento)

- Nenhuma.

## feed_posts.csv

- **Formato:** CSV, separador `,`, utf-8 · 8,9 MB
- **Uma linha por:** post (dicionário)
- **Linhas:** 119.309 · dicionário: 119.309 · confere
- **Colunas:** 5 · dicionário: 5
- **Células faltantes** (nulo, vazio ou marcador): 0 de 596.545 (0,0%)
- **Linhas duplicadas por inteiro:** 0

| Coluna | Tipo (pandas) | Conteúdo | Nulos | Vazios | Marcadores | % faltante | Distintos | Faixa ou mais frequentes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `post_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 119.309 | `f_0069439` (1); `f_0062111` (1); `f_0039963` (1) |
| `user_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 26.899 | `u_c7ce63bd` (28); `u_7e1dc669` (28); `u_c533a7dc` (26) |
| `data_hora` | str | data e hora 100,0% | 0 | 0 | 0 | 0,0% | 119.066 | 2025-07-01 06:07 a 2026-10-07 18:52 |
| `texto` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 31.620 | `funcional em casa` (4.083); `yoga pra fechar o dia` (3.982); `aula de hoje pagou` (3.925) |
| `curtidas` | int64 | inteiro 100,0% | 0 | 0 | 0 | 0,0% | 37 | 0 a 38 |

**Divergências em relação ao dicionário**

- `data_hora`: 122 linhas depois da data de corte (30/09/2026, já em horário de Brasília).

**Observações de qualidade** (não contrariam o dicionário, mas pedem tratamento)

- Nenhuma.

## tickets_suporte.csv

- **Formato:** CSV, separador `,`, utf-8 · 495 KB
- **Uma linha por:** chamado (dicionário)
- **Linhas:** 4.422 · dicionário: 4.422 · confere
- **Colunas:** 8 · dicionário: 8
- **Células faltantes** (nulo, vazio ou marcador): 1.505 de 35.376 (4,3%)
- **Linhas duplicadas por inteiro:** 0

| Coluna | Tipo (pandas) | Conteúdo | Nulos | Vazios | Marcadores | % faltante | Distintos | Faixa ou mais frequentes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `ticket_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 4.422 | `t_000368` (1); `t_000369` (1); `t_000370` (1) |
| `user_id` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 3.989 | `u_e6e21b56` (4); `u_725e3c9e` (4); `u_d6877125` (4) |
| `aberto_em` | str | data e hora 100,0% | 0 | 0 | 0 | 0,0% | 4.389 | 2025-07-01 08:15 a 2026-09-30 21:46 |
| `canal` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 3 | `chat` (2.195); `email` (1.120); `loja` (1.107) |
| `texto_cliente` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 303 | `quero cancelar minha ass…` (245); `quero o reembolso, não u…` (241); `corrida registrada com d…` (224) |
| `categoria_atendente` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 6 | `tecnico` (961); `cancelamento` (913); `conta` (757); `cobranca` (651); `conteudo` (588); `duvida_geral` (552) |
| `status` | str | texto 100,0% | 0 | 0 | 0 | 0,0% | 3 | `resolvido` (2.917); `aberto` (981); `sem_resposta` (524) |
| `resolvido_em` | str | data 100,0% | 0 | 1.505 | 0 | 34,0% | 460 | 2025-07-03 a 2026-10-07 |

**Divergências em relação ao dicionário**

- `resolvido_em`: 41 linhas depois da data de corte (30/09/2026, já em horário de Brasília).

**Observações de qualidade** (não contrariam o dicionário, mas pedem tratamento)

- Nenhuma.

## heatmaps/

Os dois zips foram listados sem descompactar. Formato e dimensões vêm do cabeçalho de uma amostra de até 50 imagens por zip, lida direto na memória.

| Zip | Tamanho | Arquivos | PNG | Dicionário | Pastas internas | Formato (amostra) | Tamanho por imagem |
|---|---:|---:|---:|---:|---|---|---|
| `heatmaps/heatmaps_2026-07-31.zip` | 51,7 MB | 12.426 | 12.426 | 12.426 | `2026-07-31/` (12.426) | PNG 192×192 px, paleta, 8 bits (37/50); PNG 192×192 px, paleta, 4 bits (13/50) | 1 KB a 9 KB |
| `heatmaps/heatmaps_2026-09-30.zip` | 54,3 MB | 13.047 | 13.047 | 13.047 | `2026-09-30/` (13.047) | PNG 192×192 px, paleta, 8 bits (29/50); PNG 192×192 px, paleta, 4 bits (21/50) | 1 KB a 9 KB |

**Divergências em relação ao dicionário**

- Nenhuma.

**Observações de qualidade**

- `heatmaps_2026-07-31.zip`: 5 arquivos de metadados do macOS (`__MACOSX/`, nomes `._…`, 1165 bytes no total). Não são imagens; ficaram fora das contagens.
- O dicionário chama a pasta de `heatmaps_90d/`. No data room ela se chama `heatmaps/`, e cada data vem num zip próprio.

## Integridade de dados/brutos/

- `amizades.csv`: inalterado (`103029d4dd434912…`)
- `assinaturas.csv`: inalterado (`29db4d815a99a543…`)
- `atividades.parquet`: inalterado (`b5269feac894938c…`)
- `campanha_ago26.csv`: inalterado (`f635ad72be045383…`)
- `eventos_assinatura.csv`: inalterado (`64032d95b6ca3aad…`)
- `feed_posts.csv`: inalterado (`0f819ad3d3254a80…`)
- `heatmaps/heatmaps_2026-07-31.zip`: inalterado (`19942958c3f445b0…`)
- `heatmaps/heatmaps_2026-09-30.zip`: inalterado (`f4ecf41b1810d3b7…`)
- `onboarding.csv`: inalterado (`03a91268b659d208…`)
- `pagamentos.csv`: inalterado (`28b12716caea413b…`)
- `pesquisa_saida.csv`: inalterado (`5534d6bf683564d3…`)
- `tickets_suporte.csv`: inalterado (`6b56d21caaebeb52…`)
- `uso_mensal.csv`: inalterado (`844db26847fb785a…`)
- `usuarios.csv`: inalterado (`c016416ec00362b0…`)
