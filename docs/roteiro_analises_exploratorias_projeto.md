# Roteiro de análises exploratórias · projeto completo

Cobre os 13 arquivos do data room e os 8 objetivos de `docs/contexto_case.md`. Complementa o `docs/roteiro_analises_exploratorias.md` (aula 2, análises 0 a 12), que continua valendo para a base de qualidade e junções.

**Regras de todas as análises**
- Antes de rodar, mostre o plano e espere a aprovação. Mostre a contagem de linhas depois de cada filtro e de cada junção.
- Corte em 30/09/2026. Nada posterior entra. Horários em UTC (Z) convertidos para Brasília. Contas @vitaliza.com.br ficam fora.
- Resuma logs por `user_id` antes de juntar. Nunca altere `dados/brutos/`.
- Use só os arquivos que a pergunta pede. Cada decisão de limpeza vai no `decisoes.md` (motivo e efeito na contagem).
- Os números de "Confira" vêm do `contexto_case.md` e do roteiro da aula 2. Se o resultado divergir, investigue antes de seguir.

## Mapa: objetivo, arquivos e fases

| Fase | Objetivo do case | Arquivos principais | Entrega |
|---|---|---|---|
| A. Base limpa | 1. Contar e medir | todos (qualidade), `usuarios`, `assinaturas`, `eventos_assinatura` | base integrada no corte + `decisoes.md` |
| B. Churn | 1 e 2 | `eventos_assinatura`, `pagamentos`, `assinaturas`, `usuarios` | série de churn e cruzamentos |
| C. Comportamento | 2 e 3 | `uso_mensal`, `atividades`, `amizades`, `feed_posts` | variáveis por assinante e segmentos |
| D. Motivos | 2 | `pesquisa_saida`, `tickets_suporte`, `onboarding` | motivos e viés de seleção |
| E. Texto e imagem | 5 | `onboarding`, `feed_posts`, `tickets_suporte`, `heatmaps` | variáveis extraídas e acerto |
| F. Campanha | 6 | `campanha_ago26`, `pagamentos` | uplift por grupo |
| G. Modelo | 4 | base integrada | previsão de saída até 29/11/2026 |
| H. Decisão e R$ | 6, 7 e 8 | tudo acima | lista de contato, retorno e mensagem |

---

## Fase A · Base limpa e integrada

### A1. Inventário e qualidade (feito)
`saidas/inventario.md` e `src/inventario.py` cobrem os 12 arquivos de dados e os heatmaps. **Confira:** 64.948 contas, 32.643 assinaturas, 275.565 eventos, 1.254.475 treinos. Divergências já listadas: datas após o corte (cadastro 119, treinos 34, posts 122, tickets 41, amizades 273), 60 contas de teste/cortesia.

### A2. Pagantes ativos no corte
Análise 1 da aula 2. **Confira:** 14.753 (14.813 é o erro de não tirar as 60 contas de teste); anual 57%, mensal 43%; App Store 36,6%, Google Play 33,6%, web cartão 20,3%, web Pix 9,5%.

### A3. Padronização de `usuarios.csv`
**Objetivo:** propor, sem aplicar ainda, o mapa de padronização.
- `sexo` (6 grafias de 2 valores), `sistema` (5 grafias de 2 valores), `cidade` (maiúsculas e acentos), `cep_prefixo` (manter como texto).
- Datas: 119 cadastros e 194 nascimentos depois do corte; `data_nascimento` com 1900-01-01 e 2031. Decidir: marcar, corrigir ou remover, e registrar o efeito na contagem.
**Confira:** soma das categorias padronizadas = total de linhas.

### A4. Situação em qualquer data pelos eventos
Análise 11 da aula 2, generalizada: função que devolve, para cada assinatura, a situação numa data (não assinava, ativo com renovação ligada, ativo com renovação desligada, encerrado).
- Converter fuso: lojas em UTC, site em Brasília.
- Assinatura anterior a 01/07/2024 não tem evento de início: tratar como ativa até o primeiro evento.
- Pela loja, entre `renovacao_automatica_desligada` e `assinatura_expirada` a pessoa ainda é assinante.
**Confira:** reconstruir 30/09/2026 e obter 14.753; reconstruir 31/07 e comparar com a análise 11 da aula 2.

### A5. Base integrada de assinantes (uma linha por assinante)
Análise 7 da aula 2 como modelo. Resumir `atividades`, `uso_mensal`, `pagamentos`, `tickets_suporte`, `feed_posts` e `amizades` por `user_id` antes de juntar.
**Confira:** uma linha por `user_id` depois de cada junção; sem multiplicar linhas. Salvar em `dados/processados/`.

---

## Fase B · Churn (objetivos 1 e 2)

### B1. Churn mensal oficial
**Pergunta:** reproduzir a série mensal (perdas no mês ÷ ativos no início do mês), jan/2025 a set/2026.
**Confira:** 5,6% em média em 2025; 6,6% em jan a set/2026; abril/2026 = 1.154 perdas sobre 14.237 ativos (8,1%); agosto 5,9%; setembro 5,0%. A série tem 3.362 perdas em jun a set, contra 3.389 fins de assinatura (assinaturas que começam e terminam no mesmo mês ficam fora da série).

### B2. Voluntário × falha de cobrança
**Arquivos:** `pagamentos.csv` (165.548 tentativas) e `eventos_assinatura.csv`.
- Resumir por assinatura: tentativas, recusas, estornos, chargebacks, `periodo_carencia`.
- Separar saída voluntária (renovação desligada, cancelamento) de involuntária (cobrança recusada até expirar).
**Confira:** contagem por `status` e `metodo`; a soma das saídas por tipo bate com o total de fins.

### B3. Churn por plano, canal, tempo de casa e aquisição
**Pergunta:** a subida de 2026 vem de um grupo específico?
- Taxa de churn mensal por plano (referência da aula 1: 9,0% mensal × 2,6% anual em 2025), canal de cobrança, canal de aquisição, tempo de casa e relógio conectado.
- Mostrar o tamanho de cada grupo. O anual só pode sair no aniversário: comparar com cuidado.
- Testar a terceira variável (plano) em cada diferença.

### B4. Os três fatos de 2026
**Pergunta:** reajuste (01/03/2026), pesquisa de saída (01/06/2026) e campanha (10/08/2026): algum aparece na série?
- Churn do mensal × anual antes e depois de 01/03/2026 (o reajuste só atinge o mensal).
- Churn de quem paga pela loja × site depois de 01/06.
- Abril/2026 como pior mês: quem saiu e de que plano.
**Atenção:** é cruzamento, aponta suspeitos e não prova causa.

---

## Fase C · Comportamento (objetivos 2 e 3)

### C1. Temporalidade e cinco números de `uso_mensal.csv`
Análises 6, 8 e 10 da aula 2. **Confira:** 2025 sem linhas zeradas; jan/2026 com 41.130 linhas e 25.697 com zero; set/2026 com 56.565 linhas, média 82,6 min, mediana 0, 72,3% com zero, CV 268%.

### C2. Qualidade e distribuição de `atividades.parquet`
Análises 3, 4, 5 e 9 da aula 2. **Confira:** 951 treinos acima de 200 km; 11 valores de `tipo` para 7 tipos; 9.383 treinos em dobro (4.184 `apple_health` e 5.199 `garmin`, só com o fuso corrigido); mediana 6,47 km.

### C3. Variáveis de comportamento antes do corte
Para cada assinante, medidas calculadas só com informação até a data de referência: dias ativos, minutos e treinos nos últimos 30 e 90 dias, queda de uso (últimos 30 dias contra os 60 anteriores), tipo de treino predominante, relógio, dias sem treinar.
**Confira:** nenhuma data posterior à referência; contas sem treino ficam com zero, não nulo.

### C4. Rede social: `amizades.csv` e `feed_posts.csv`
- Por conta: seguidores, seguidos, reciprocidade (a relação é de mão única), posts e curtidas no período.
- 273 amizades e 122 posts depois do corte: marcar e excluir.
- Pergunta: quem tem amigos assinantes sai menos? Cruzar com o churn e conferir a terceira variável (tempo de casa).

### C5. Segmentação sem usar a saída (objetivo 3)
- Escolher variáveis de uso, plano, tempo de casa e rede; padronizar escalas; ver correlações antes (análise 10 da aula 2).
- Clusterizar sem a variável de saída, definir o número de grupos por silhueta e interpretação de negócio, e depois cruzar cada segmento com o churn.
**Confira:** cada segmento tem tamanho mínimo razoável e é descrito em uma frase de negócio.

---

## Fase D · Motivos de saída (objetivo 2)

### D1. Pesquisa de saída e viés de seleção
**Arquivo:** `pesquisa_saida.csv` (643 respostas de 641 contas).
- Duplicados: 2 contas com mais de uma resposta; decidir qual vale.
- 289 respostas são de quem seguia ativo no corte: separar de quem saiu.
- Distribuição de `motivo_principal` entre quem saiu.
- **Armadilha:** só quem paga pelo site vê a pesquisa. Em jun a set/2026 houve 3.389 fins (2.271 loja, 1.118 site) e 353 respostas. Não generalizar para os ~70% que pagam pela loja.

### D2. Tickets de suporte
**Arquivo:** `tickets_suporte.csv` (4.422 chamados).
- Chamados por conta, canal, `categoria_atendente`, `status`, tempo de resolução (41 `resolvido_em` depois do corte: tratar).
- Quem abriu chamado sem resposta sai mais? Cruzar com o churn e conferir o tempo de casa.

---

## Fase E · Texto e imagem (objetivo 5)

Usar só uma amostra pequena em cada teste e medir o custo antes de escalar. Não rodar a base inteira de uma vez.

### E1. Texto: onboarding, posts e tickets
- Definir as variáveis a extrair (por exemplo: objetivo declarado, tema da reclamação, tom do post).
- Extrair com IA generativa numa amostra, rotular à mão a mesma amostra e medir o acerto e o custo por registro.
- `onboarding.csv`: tratar `nivel` e `dias_por_semana` (vazios sem aviso no dicionário) e `objetivo_texto` (8,6% vazio, opcional).
- **Chaves e senhas:** nunca colocar em arquivo do projeto; usar variável de ambiente.

### E2. Imagem: heatmaps
- Há 2 zips (31/07 com 12.426 imagens e 30/09 com 13.047). Só existem para pagantes que treinaram ao ar livre.
- Contar pixels por cor (verde parque, azul água, areia praia, amarelo avenida) como linha de base e comparar com a extração por IA.
- Usar o heatmap de 31/07 para prever a saída depois, e o de 30/09 só para os modelos que olham para frente.

### E3. Valor das variáveis novas
Comparar o desempenho do modelo da Fase G com e sem as variáveis de texto e imagem. Registrar acerto, custo e ganho.

---

## Fase F · Campanha de 10/08/2026 (objetivo 6)

### F1. Verificar o sorteio
**Arquivo:** `campanha_ago26.csv` (14.120 pagantes em 4 grupos).
- Tamanho de cada grupo e equilíbrio de plano, canal, tempo de casa e uso antes de 10/08. Se o sorteio foi aleatório, os grupos devem ser parecidos.
- Taxas de abertura e clique por canal (push e e-mail).

### F2. Uplift
- Saída até 30/09 por grupo contra o controle. Diferença, intervalo e tamanho de cada grupo.
- Abrir por plano (a oferta é diferente: 30% por 3 meses no mensal e 1 mês grátis no anual) e por canal de cobrança.
- Cuidado: oferta de desconto reduz a receita de quem ficaria de qualquer jeito.

---

## Fase G · Previsão de saída (objetivo 4)

- Alvo: sair até 29/11/2026 (60 dias depois do corte). Referência de treino: pagantes numa data anterior e quem saiu depois.
- **Sem vazamento:** variáveis medidas só até a data de referência. Não usar `assinaturas.csv` (retrato de 01/10) para a situação passada; o erro da análise 11 da aula 2 mostra o tamanho do vazamento.
- Validação com separação no tempo, não aleatória.
- Ordem: regressão logística como referência, depois árvore, bagging e boosting. Comparar por métrica de ranking e por taxa de acerto dos 1.500 mais prováveis.

---

## Fase H · Decisão, retorno e mensagem (objetivos 6, 7 e 8)

### H1. Quem contatar
- Classificar em persuadíveis, garantidos, perdidos e não-perturbe (Siegel), cruzando a previsão de saída com o uplift da Fase F.
- Respeitar os tetos: 1.500 WhatsApp e 300 CS por mês, push máximo de 1 por semana por pessoa.

### H2. Retorno em R$
- Receita incremental líquida contra não fazer nada: taxas (loja 15%, cartão 3,5%, Pix 0,99%), custo de servir R$ 4,20 por mês, custos de contato (e-mail R$ 0,01, WhatsApp R$ 0,40, CS R$ 18,00) e das ofertas (mensal R$ 35,91, anual R$ 25,00).
- Orçamento de R$ 40.000 por mês, com descontos e IA generativa incluídos.

### H3. Mensagem
Escrever o briefing e gerar a mensagem com IA generativa para cada segmento. Conferir tom, oferta correta para o plano e se a pessoa não está no grupo "não-perturbe".

---

## Ordem de execução sugerida

1. **A1 a A5** (base limpa e integrada). Tudo o resto depende disso.
2. **B1 a B4** e **C1 a C3** em paralelo, porque usam arquivos diferentes.
3. **C4, C5, D1 e D2.**
4. **F1 e F2** (independente das outras fases, só precisa da base).
5. **E1 a E3**, depois **G**, depois **H1 a H3**.

**Pontos de parada:** ao fim de cada fase, rodar de novo, conferir três números à mão e atualizar o `decisoes.md` antes de seguir.
