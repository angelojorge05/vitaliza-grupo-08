# Contexto do case Vitaliza (resumo dos PDFs)

Fonte: `docs/Vitaliza - Enunciado do case.pdf` e `docs/Vitaliza - Dicionário de dados.pdf`.
Em caso de dúvida, o PDF manda.

## A empresa
- App brasileiro de assinatura para quem treina, lançado em set/2020 (fictício). Três partes: treino ao ar livre com GPS (corrida, caminhada, pedal), treinos em vídeo (funcional, força, yoga) e rede social (posts, comentários, seguidores). Cerca de 4 em 10 contas têm relógio conectado (Garmin, Apple Watch).
- Freemium: registrar treino é grátis. O Premium tem 7 dias de teste.
- Preços: mensal R$ 34,90 até 28/02/2026 e R$ 39,90 desde 01/03/2026; anual R$ 299,90 (R$ 239,90 no 1º ano para quem chega por cupom de influenciador). Renovação automática.
- Base: 64.948 contas cadastradas. Assinantes pagantes: 8.540 no início de jan/2025, cerca de 13.200 no fim de 2025, 14.319 no início de set/2026 e **14.753 em 30/09/2026**.
- Dos ativos no corte: 57% anual e 43% mensal. Canal de cobrança: App Store 36,6%, Google Play 33,6%, web cartão 20,3%, web Pix 9,5%.
- Canais de aquisição: orgânico, influenciadores, anúncios, indicação, parcerias com empresas.

## A métrica oficial: churn mensal
- Churn mensal = assinaturas perdidas no mês ÷ ativos no início do mês.
- Média de 5,6% ao mês em 2025 e de 6,6% em jan–set/2026. Pior mês: abr/2026, com 1.154 perdas sobre 14.237 ativos (8,1%). Ago/2026: 5,9%. Set/2026: 5,0%.
- Esses números servem de **referência para conferir** nossas contas.

## As quatro lacunas
1. **Por que o churn subiu em 2026.** Há três fatos no período, nenhum testado como causa: o reajuste do mensal (01/03/2026), o início da pesquisa de saída (01/06/2026) e a campanha de retenção (10/08/2026).
2. **Por que cada um saiu.** Quem paga pela loja cancela fora do app. A Vitaliza recebe só dois avisos, sem motivo: `renovacao_automatica_desligada` e depois `assinatura_expirada`, no fim do período pago. Só quem paga pelo site vê a pesquisa de saída. Em jun–set/2026 houve 3.389 fins de assinatura (2.271 pela loja, 1.118 pelo site) e só 353 respostas: **viés de seleção**. Para os ~70% que pagam pela loja, é preciso agir antes, a partir de sinais de uso, ou entre os dois avisos.
3. **Se a campanha de 10/08/2026 funcionou.** Os 14.120 pagantes daquele dia foram sorteados em 4 grupos: desafio, cupom (30% por 3 meses no mensal, 1 mês grátis no anual), conteúdo e controle. É um experimento aleatorizado que **nunca foi analisado**, e serve de base para estimar o uplift.
4. **Quem contatar.** O CRM tem teto de 1.500 WhatsApp e 300 atendimentos de CS por mês.

## Objetivos (em ordem, cada um usa o anterior)
1. **Contar e medir a base:** ativos no corte, churn por mês, plano e canal. Inclui a qualidade de cada arquivo, a junção por `user_id` e a reconstrução da situação numa data a partir dos eventos.
2. **Explicar a subida de 2026:** hipóteses (plano, canal, tempo de casa, frequência de treino, preço) testadas por cruzamentos. Cruzamento aponta suspeitos, não prova causa.
3. **Segmentar:** clusterização sem usar a variável de saída.
4. **Prever a saída em 60 dias após o corte (até 29/11/2026):** regressão logística como referência, depois árvore, bagging e boosting. Validação com separação no tempo e **sem vazamento** (nada posterior ao corte).
5. **Valor de texto e imagem:** extrair variáveis com IA generativa (onboarding, posts, tickets, heatmaps), conferir contra uma amostra rotulada à mão e medir acerto e custo. Nas imagens, comparar com contagem de pixels por cor. Comparar modelos com e sem essas variáveis.
6. **Decidir quem contatar:** persuadíveis × garantidos × perdidos × não-perturbe (Siegel). Uplift estimado pela campanha de agosto.
7. **Calcular o retorno em R$** contra não fazer nada: só a receita incremental, menos contatos e ofertas.
8. **Escrever a mensagem** com IA generativa, a partir de um briefing.

## Premissas de negócio (para as contas em R$)
- Taxas: loja 15%, cartão 3,5%, Pix 0,99%. Receita líquida do mensal de R$ 39,90: loja R$ 33,92, cartão R$ 38,50, Pix R$ 39,50. Anual pela loja: R$ 254,92.
- Custo de servir: R$ 4,20 por mês por assinante. CAC em 2026: R$ 118.
- Canais: push grátis (máx. 1 por semana por pessoa), e-mail R$ 0,01, WhatsApp R$ 0,40 (teto de 1.500 por mês), CS R$ 18,00 (teto de 300 por mês).
- Ofertas: mensal com 30% por 3 meses (custo R$ 35,91); anual com 1 mês grátis (R$ 25,00); pausa de até 60 dias (receita adiada); plano personalizado (sem custo direto).
- Orçamento de CRM: **R$ 40.000 por mês**, incluindo descontos e o custo de IA generativa.

## Data room (exportado em 01/10/2026, sem limpeza)
Formatos de data, fuso, maiúsculas e categorias variam entre arquivos. Conferir a qualidade faz parte do trabalho. O `user_id` liga tudo.

| Arquivo | Forma | Uma linha por | Linhas esperadas | Período / observações |
|---|---|---|---|---|
| usuarios.csv | tabela | conta | 64.948 | user_id, email, data_cadastro, data_nascimento, sexo, cidade, uf, cep_prefixo, canal_aquisicao, sistema, versao_app, relogio_conectado. Campos digitados, sem validação |
| assinaturas.csv | tabela | assinatura | 32.643 | **Retrato de 01/10/2026** (campos sobrescritos, não é histórico). assinatura_id, user_id, plano_atual, canal_cobranca (app_store/google_play/web_cartao/web_pix), inicio, status_atual, renovacao_automatica, data_fim, motivo_fim |
| amizades.csv | tabela | relação de seguir | 113.480 | seguidor_id, seguido_id, desde (relação de mão única) |
| campanha_ago26.csv | tabela | assinante sorteado | 14.120 | user_id, grupo (controle/desafio/cupom/conteudo), enviado_em, canal, titulo_mensagem, oferta (30pct_3_meses/1_mes_gratis), abriu_push, abriu_email, clicou |
| eventos_assinatura.csv | log | evento | 275.565 | **Desde 01/07/2024.** Fonte para reconstruir a situação numa data. data_hora: **lojas em UTC (Z), site em horário de Brasília**. Eventos: trial_iniciado, trial_expirado, assinatura_iniciada, renovacao, renovacao_automatica_desligada, renovacao_automatica_religada, periodo_carencia, assinatura_expirada, cancelamento_web, reembolso, chargeback. Também plano, canal_cobranca, detalhe |
| pagamentos.csv | log | tentativa de cobrança | 165.548 | pagamento_id, user_id, data_hora, valor, metodo (app_store/google_play/cartao/pix_automatico), status (aprovado/recusado/estornado/chargeback), tentativa. Separa saída voluntária de falha de cobrança |
| uso_mensal.csv | log | usuário × mês | 591.662 | jan/2025–set/2026. mes (AAAA-MM), atividades, atividades_ar_livre, atividades_video, minutos, dias_ativos, sessoes_app |
| atividades.parquet | log | treino | 1.254.475 | 01/01–30/09/2026. atividade_id, user_id, inicio (fuso como veio da origem), tipo, duracao_min, distancia_km, ritmo_min_km, fc_media, origem (app/garmin/apple_health), gps_ok, treino_com |
| onboarding.csv | texto | conta | 63.929 | onboarding_id, user_id, respondido_em, objetivo_texto (livre, opcional), como_conheceu (livre), nivel, dias_por_semana (texto livre) |
| pesquisa_saida.csv | texto | resposta | 643 (de 641 contas) | Desde 01/06/2026, só para quem cancela pelo site. motivo_principal (preco/nao_uso/problema_tecnico/outro_app/saude/outro), comentario. 289 respostas são de quem seguia ativo no corte |
| feed_posts.csv | texto | post | 119.309 | 01/07/2025–30/09/2026. post_id, user_id, data_hora, texto, curtidas |
| tickets_suporte.csv | texto | chamado | 4.422 | Desde 01/07/2025. ticket_id, user_id, aberto_em, canal (chat/email/loja), texto_cliente, categoria_atendente, status (resolvido/aberto/sem_resposta), resolvido_em |
| heatmaps/ (2 zips) | imagem | assinante × data | 12.426 (31/07) + 13.047 (30/09/2026) | `<user_id>.png`, rotas dos 90 dias até a data. Só existe para quem era pagante e treinou ao ar livre. Cores do fundo: verde parque, azul água, areia praia, amarelo avenida |

## Armadilhas já conhecidas
- O churn da série mensal (3.362 perdas em jun–set) e os fins de assinatura (3.389) medem coisas diferentes: a série deixa de fora as assinaturas que começam e terminam no mesmo mês.
- `assinaturas.csv` não serve para a situação no passado: usar `eventos_assinatura.csv`.
- Assinaturas anteriores a 01/07/2024 não têm eventos.
- Pela loja, entre o desligamento da renovação e a expiração, a pessoa **ainda é assinante**.
- Fusos misturados: converter tudo para horário de Brasília.
- Contas de teste (@vitaliza.com.br) ficam fora.
