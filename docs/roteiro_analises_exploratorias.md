# Roteiro de análises exploratórias · Aula 2 (22/10/2026)

Extraído do PDF da aula 2 (MBA em IA e Dados para Negócios, Módulo 2). Cada item traz o objetivo, o prompt dos slides e o que conferir. Os valores de "Confira" são os dos slides: se o agente devolver outro número, desconfie antes de acreditar.

**Adaptações para o nosso projeto**
- Os prompts dos slides citam `docs/dicionario_dados.md`. Aqui o dicionário é `docs/Vitaliza - Dicionário de dados.pdf`: troque o nome do arquivo no prompt.
- Os slides citam `AGENTS.md` (Codex). No Claude Code o arquivo de contexto é o `CLAUDE.md`.
- Todo pedido começa com "Mostre o plano antes de rodar" e termina com "Não altere nada em dados/brutos/". Aprove o plano antes de o agente executar.
- Depois de cada resultado: leia o código, rode de novo, cheque três números à mão e compare com o dicionário.
- Cada decisão de limpeza (corrigir, remover ou marcar) vai no `decisoes.md`, com o motivo e o efeito na contagem.

## Ordem sugerida

| # | Análise | Arquivo | Seção da aula |
|---|---|---|---|
| 0 | Inventário | todos de `dados/brutos/` | O ambiente |
| 1 | Pagantes ativos no corte | `assinaturas.csv`, `usuarios.csv` | Pedir e conferir |
| 2 | Completude | `onboarding.csv` | Qualidade |
| 3 | Validade | `atividades.parquet` | Qualidade |
| 4 | Consistência | `atividades.parquet` | Qualidade |
| 5 | Unicidade | `atividades.parquet` | Qualidade |
| 6 | Temporalidade | `uso_mensal.csv` | Qualidade |
| 7 | Juntar sem multiplicar | `usuarios.csv`, `atividades.parquet` | Granularidade |
| 8 | Os cinco números | `uso_mensal.csv` | Estatística descritiva |
| 9 | Histograma, quartis e extremos | `atividades.parquet` | Distribuições |
| 10 | Correlação e terceira variável | `uso_mensal.csv` | Correlação |
| 11 | Retrato e histórico | `assinaturas.csv`, `eventos_assinatura.csv`, `usuarios.csv` | Retrato e histórico |
| 12 | Prática principal (7 passos) | vários | Na prática |

---

## 0. Inventário dos arquivos (O primeiro pedido)

**Objetivo:** ver se o agente segue o contexto antes de tocar nos dados e saber o que há em cada arquivo.

```
Leia o AGENTS.md antes de começar.
Quero um inventário de dados/brutos/, sem alterar nada.
Para cada arquivo: linhas, colunas, tipos e vazios.
Em heatmaps_90d/, só quantos arquivos há e o formato.
Compare com o dicionário em docs/ e liste as divergências.
Antes de executar, mostre o plano e espere a aprovação.
Salve em saidas/inventario.md, uma seção por arquivo.
```

**Confira:**
- O plano vem antes de qualquer comando e repete as regras do contexto, como o corte em 30/09/2026.
- Uma seção para cada um dos 12 arquivos de dados.
- `usuarios.csv` com 64.948 linhas (o `wc -l` dá 64.949, com o cabeçalho); `atividades.parquet` com 1.254.475.
- Nada mudou em `dados/brutos/`.

---

## 1. Um pedido completo: pagantes ativos no corte

**Objetivo:** contar os pagantes ativos no corte com um pedido nas cinco partes (pergunta, arquivos, regras, saída, critério de pronto) e conferir o número antes de acreditar.

```
Pergunta: quantos assinantes pagantes ativos a Vitaliza tinha
no corte, 30/09/2026?
Arquivos: dados/brutos/assinaturas.csv e
dados/brutos/usuarios.csv, com o dicionário em docs/.
Regras: contas de teste (e-mail @vitaliza.com.br) não contam;
mostre as linhas depois de cada filtro; não altere nada em
dados/brutos/.
Saída: o número, a tabela de filtros e o código em notebooks/.
Pronto quando: a soma por plano e por canal bate com o total.
Antes de rodar, mostre o plano e espere a aprovação.
```

**Confira:**
- 14.753 pagantes ativos (o número do LEIA-ME).
- Anual 57% e mensal 43%; App Store 36,6% e Google Play 33,6%.
- **Armadilha:** 14.813 é o retrato sem tirar as 60 contas de teste.
- Cheque à mão três contas do resultado.

---

## Qualidade de dados: as cinco dimensões (Wang e Strong, 1996)

Completude, validade, consistência, unicidade e temporalidade. O slide de resumo traz um exemplo da base por dimensão.

### 2. Completude: 8,6% sem objetivo

**Objetivo:** medir quanto falta em cada coluna e separar o vazio opcional do vazio que é problema.

```
Leia docs/Vitaliza - Dicionário de dados.pdf
Mostre o plano antes de rodar.
Em dados/brutos/onboarding.csv:
1. conte as linhas e os user_id únicos;
2. em cada coluna, conte os vazios: nulos e textos só com
espaços, separados;
3. mostre o percentual, da coluna mais vazia para a menos
vazia;
4. diga quais colunas o dicionário marca como opcionais.
Não altere nada em dados/brutos/.
```

**Confira:**
- 63.929 respostas, uma por conta.
- `objetivo_texto`: 5.467 vazias (8,6%), todas nulas; nenhuma só com espaços.
- Opcionais no dicionário: `objetivo_texto` e `como_conheceu`.
- **Armadilha:** `nivel` (7,1%) e `dias_por_semana` (10,0%) também têm vazios, e o dicionário não diz que são opcionais.

### 3. Validade: 951 treinos acima de 200 km

**Objetivo:** achar distâncias e durações de treino que não podem ser reais, sem confundir com o que só está vazio.

```
Leia docs/dicionario_dados.md.
Mostre o plano antes de rodar.
Em dados/brutos/atividades.parquet (pandas e pyarrow):
1. conte os treinos e quantos têm distancia_km preenchida;
2. mostre mínimo, mediana e máximo de distancia_km e
duracao_min;
3. conte os treinos acima de 200 km e os com duração zero ou
negativa;
4. liste os cinco mais longos, com todas as colunas.
Não altere nada em dados/brutos/.
```

**Confira:**
- 1.254.475 treinos; 679.640 com distância.
- Mediana 6,47 km; 951 acima de 200 km. O maior, 10.012,75 km, é um pedal de 160 minutos do `apple_health`.
- 3.649 treinos com duração zero; nenhum negativo.
- **Armadilha:** os 574.835 sem distância não são erro; não tinham GPS.

### 4. Consistência: corrida e run

**Objetivo:** ver se a mesma categoria aparece escrita de mais de um jeito na coluna `tipo`.

```
Leia docs/dicionario_dados.md.
Mostre o plano antes de rodar.
Em dados/brutos/atividades.parquet:
1. liste os valores de tipo, com a contagem de cada um;
2. cruze tipo com origem;
3. aponte os valores que parecem a mesma categoria e proponha
um mapa de padronização, sem aplicar;
4. mostre quantas linhas cada troca afetaria.
Não altere nada em dados/brutos/.
```

**Confira:**
- 11 valores para 7 tipos: corrida e run, caminhada e walk, força e strength, pedal e ride.
- Os nomes em inglês (376.930 treinos, 30%) vêm todos da origem `app`.
- **Armadilha:** contar só `corrida` deixa fora 162.108 corridas.

### 5. Unicidade: 9.383 treinos em dobro

**Objetivo:** contar os treinos que chegaram duas vezes, uma pelo app e outra pelo relógio.

```
Leia docs/dicionario_dados.md.
Mostre o plano antes de rodar e diga como vai tratar o horário
de cada origem.
Em dados/brutos/atividades.parquet:
1. ache os pares da mesma conta, mesmo tipo e mesma duração,
com início a até 5 minutos, um de origem app e outro de garmin
ou apple_health;
2. conte os pares por origem;
3. mostre cinco pares lado a lado.
Não remova nada nem altere dados/brutos/.
```

**Confira:**
- 9.383 pares: 4.184 com o `apple_health` e 5.199 com o `garmin`.
- Nos pares, a distância também é igual.
- **Armadilha:** o `garmin` grava o início 3 horas à frente (UTC). Sem corrigir o fuso, só aparecem os 4.184 do `apple_health`.

### 6. Temporalidade: ausente em 2025, zero em 2026

**Objetivo:** ver se o mês sem treino é registrado do mesmo jeito em 2025 e em 2026, antes de comparar médias.

```
Leia docs/dicionario_dados.md.
Mostre o plano antes de rodar.
Em dados/brutos/uso_mensal.csv, para cada mês de jan/2025 a
set/2026:
1. conte as linhas e as linhas com minutos = 0;
2. calcule a média e a mediana de minutos;
3. explique o que muda na virada de 2025 para 2026 e o efeito
disso numa média calculada sobre o arquivo como está.
Não altere nada em dados/brutos/.
```

**Confira:**
- 2025: nenhum mês com linha zerada; dez/2025 tem 13.624 linhas.
- jan/2026: 41.130 linhas, 25.697 com zero.
- A média cai de 265 para 118 minutos na virada só por isso; contando só quem treinou, jan/2026 dá 314.

---

## 7. Granularidade: contar antes e depois (juntar sem multiplicar)

**Objetivo:** juntar os treinos às contas sem multiplicar linhas, contando antes e depois da junção. Resumir o log por assinante antes de juntar.

```
Leia docs/dicionario_dados.md.
Mostre o plano antes de rodar, com o grão de cada arquivo.
Quero uma linha por conta de dados/brutos/usuarios.csv, com os
treinos e os minutos de dados/brutos/atividades.parquet:
1. conte as linhas de cada arquivo;
2. resuma os treinos por user_id antes de juntar;
3. junte pela esquerda e conte as linhas depois;
4. confirme que há um user_id por linha;
5. deixe com zero as contas sem treino.
Salve em dados/processados/. Não altere nada em dados/brutos/.
```

**Confira:**
- 64.948 contas e 1.254.475 treinos.
- Juntar o log direto daria 1.282.872 linhas: as contas se repetem.
- Resumindo antes: 36.551 contas com treino; depois da junção, 64.948 linhas, 28.397 com zero.
- **Armadilha:** mais linhas que contas no resultado é sinal de que a junção multiplicou.

Grão de cada arquivo: `usuarios.csv` (conta), `assinaturas.csv` (assinatura), `eventos_assinatura.csv` (evento), `atividades.parquet` (treino), `uso_mensal.csv` (mês).

---

## Estatística descritiva

Conceitos dos slides (sem prompt próprio): **amostra** (cada sorteio de 500 contas dá uma média diferente; amostra que não foi sorteada engana, como a pesquisa de saída, que só tem respostas de quem paga pelo site: as lojas são 67% dos fins e nenhuma resposta veio delas); **média, mediana e moda** (o extremo puxa a média, a mediana fica); **desvio padrão** (distância típica até a média, com n − 1) e **coeficiente de variação** (CV = s / média, compara variáveis em escalas diferentes); **taxas** (toda taxa precisa do denominador certo; churn mensal = perdas no mês / ativos no início do mês).

### 8. Os cinco números, pedidos ao agente

**Objetivo:** descrever os minutos por conta com centro e dispersão e achar a medida da conta típica.

```
Leia docs/dicionario_dados.md.
Mostre o plano antes de rodar.
Em dados/brutos/uso_mensal.csv, só mes = 2026-09:
1. conte as linhas e os user_id únicos;
2. para minutos, calcule média, mediana, moda, desvio padrão e
coeficiente de variação, dizendo se dividiu por n ou por n − 1;
3. calcule a proporção de contas com zero;
4. diga em duas frases qual medida descreve a conta típica e
por quê.
Não altere nada em dados/brutos/.
```

**Confira:**
- 56.565 linhas, uma por conta.
- Média 82,6 min; mediana 0; moda 0; 72,3% das contas com zero.
- Desvio padrão 221,3 min e CV de 268%: o desvio é maior que a média.
- **Armadilha:** se a conta típica treina 83 minutos, a resposta leu só a média.

---

## Distribuições

Conceitos dos slides: tabela de frequências vira histograma; percentil é posição na lista ordenada (posição = p × (n − 1) + 1); o boxplot nasce do histograma (Q1, mediana, Q3, IQR e os pontos além do limite); na curva normal, 68, 95 e 99,7%; a média vai para o lado da cauda (frequência cardíaca é simétrica; minutos por conta e dias ativos são à direita).

### 9. Histograma, quartis e extremos, pedidos ao agente

**Objetivo:** ver a forma da distância dos treinos e marcar os extremos por duas regras, sem apagar nada.

```
Leia docs/dicionario_dados.md.
Mostre o plano antes de rodar.
Em dados/brutos/atividades.parquet, só treinos com
distancia_km preenchida:
1. conte os treinos;
2. faça a tabela de frequências e o histograma em classes de
5 km, a última com 60 km ou mais;
3. calcule Q1, mediana, Q3 e IQR;
4. marque os extremos pela regra Q3 + 1,5 × IQR e por |z| > 3,
com a contagem por tipo em cada regra.
Não remova nada nem altere dados/brutos/.
```

**Confira:**
- 679.640 treinos; 45,9% entre 5 e 10 km.
- Q1 4,58 km; mediana 6,47; Q3 9,58; IQR 5,00.
- 1,5 × IQR: 81.775 treinos acima de 17,08 km, 73.120 de pedal (com `ride`).
- |z| > 3: 956 acima de 191,6 km. **A regra marca; o grupo decide.**

---

## Correlação

Conceitos dos slides: o r soma os produtos dos desvios; vai de −1 a 1 e só vê reta; um punhado de erros derruba o r (nas corridas, o r da base cai de 0,88 para 0,12 com os 555 treinos acima de 200 km); correlação não é causa (terceira variável, seleção, causalidade reversa, coincidência); cruzamento aponta suspeitos e não prova causa.

### 10. A correlação sobrevive a uma terceira variável?

**Objetivo:** validar se quem abre mais o app treina mais minutos ou se os dois só seguem o número de treinos.

```
Leia dicionario_dados.md e me mostre o plano antes de rodar.
Em uso_mensal.csv, só mes = 2026-09 e dias_ativos > 0:
1. conte linhas e contas (user_id únicos);
2. calcule o r de Pearson entre sessoes_app e minutos;
3. calcule o mesmo r dentro de cada valor de atividades e a
média ponderada pelo número de contas;
4. calcule o r parcial de sessoes_app e minutos controlando
atividades.
Mostre as contagens de cada passo. Não altere nada em
dados/brutos/.
```

**Confira:**
- 15.685 contas com treino em setembro de 2026, de 56.565 linhas no mês.
- r de sessões e minutos: 0,88 (0,92 com quem não treinou).
- Por número de atividades e no r parcial, cai para 0,02: não sobrevive.
- **Armadilha:** faixas largas de atividades deixam a terceira variável vazar (r de 0,36 a 0,67).

---

## Retrato e histórico

### 11. Pelos eventos, 823 respostas mudam

**Objetivo:** reconstruir pelos eventos a situação da renovação em 31/07 e medir o erro de usar o retrato de 01/10 (vazamento de dados, Kaufman et al., 2012).

```
Leia docs/dicionario_dados.md.
Mostre o plano antes de rodar e diga como vai tratar o fuso.
1. Em dados/brutos/assinaturas.csv, separe as ativas com
renovacao_automatica = nao, sem as contas de teste (e-mail
@vitaliza.com.br em usuarios.csv), e conte;
2. para cada uma, reconstrua por eventos_assinatura.csv a
situação em 31/07/2026: ainda não assinava, renovação ligada
ou desligada;
3. mostre a contagem de cada situação.
Não altere nada em dados/brutos/.
```

**Confira:**
- 2.250 assinantes no retrato com a renovação desligada.
- Em 31/07: 1.427 já com a renovação desligada, 754 com ela ligada e 69 que ainda não assinavam.
- O retrato erraria 823 (37%): é o tamanho do vazamento.
- **Armadilha:** assinatura anterior a 01/07/2024 não tem evento de início; sem desligamento até 31/07, a renovação estava ligada.

---

## 12. Prática principal (30 minutos, em grupo)

**Pergunta:** entre quem pagava em 30/06/2026, quem saiu até 30/09 se comportava diferente de quem ficou? Quais duas características mais separam os dois grupos, e por que cada uma pode ser só correlação?

**Definições:** base = quem pagava a assinatura em 30/06/2026; saiu = a assinatura terminou entre 01/07 e 30/09/2026; ficou = seguia assinante em 30/09/2026. Candidatas: uso, plano, canal de cobrança, tempo de casa, aquisição, onboarding, suporte.

**Funções:** Piloto (escreve os pedidos e aprova o plano), Auditor (confere as contagens e três assinantes à mão), Relator (registra no `decisoes.md` e escreve as três frases).

**Entrega mínima:** uma tabela (os dois grupos lado a lado: tamanho, taxa de saída, centro e dispersão de cada característica), um gráfico (a distribuição da característica que mais separa, nos dois grupos), três frases (o que o dado diz, o que ele não diz e a próxima pergunta, cada uma com um número) e o `decisoes.md`.

| Passo | Tempo | O que fazer |
|---|---|---|
| 1. Definir os grupos | 5 min | Pelos eventos: quem pagava em 30/06 e quem saiu até 30/09 |
| 2. Conferir a qualidade | 3 min | Só os arquivos que a pergunta usa, pelas cinco dimensões |
| 3. Uma linha por assinante | 5 min | Tudo medido antes de 01/07, sem multiplicar linhas |
| 4. Comparar os grupos | 6 min | Mediana, quartis, distribuição e taxa por categoria |
| 5. Testar uma terceira variável | 5 min | A diferença se mantém quando se abre pelo plano? |
| 6. Registrar as decisões | 2 min | Cada escolha no `decisoes.md`, com o efeito na contagem |
| 7. Escrever as três frases | 4 min | O que o dado diz, o que não diz e a próxima pergunta |

Só os passos 1 e 5 têm prompt no PDF; os demais estão no roteiro do professor.

### Passo 1: definir os grupos

**Objetivo:** separar quem saiu de quem ficou pela data dos eventos.

```
Leia o AGENTS.md. Não altere nada em dados/brutos/.
Use dados/brutos/eventos_assinatura.csv, com os horários em Z
(UTC) convertidos para Brasília, e marque cada user_id:
base = pagava em 30/06/2026 (evento com plano preenchido até
30/06 e nenhum fim até 30/06);
saiu = da base, teve assinatura_expirada, reembolso ou
chargeback de 01/07 a 30/09/2026; ficou = o resto da base.
Mostre o plano antes de rodar e, depois, as contagens de cada
etapa. Salve dados/processados/grupos.csv (user_id, saiu).
```

**Confira:** saiu mais ficou dá a base; a taxa fica perto de três meses de churn do LEIA-ME; três `user_id` conferidos à mão no arquivo.

### Passo 5: a terceira variável

**Objetivo:** ver se a diferença sobrevive a uma terceira variável.

```
Use dados/processados/assinantes.csv. Não altere nada em
dados/brutos/.
Pegue as duas características que mais separaram quem saiu de
quem ficou e abra cada uma por uma terceira variável: o plano
(mensal e anual) ou, se for o próprio plano, o mês de
aniversário da assinatura. Mostre a taxa de saída e o tamanho
de cada subgrupo. A diferença se mantém, diminui, some ou
inverte?
Para quem saiu, mostre quando foi o
renovacao_automatica_desligada em relação a abril a junho de
2026.
Mostre o plano antes de rodar.
```

**Confira:** subgrupo quase sem saídas: ele podia sair no período? A renovação foi desligada antes ou depois do uso medido?

---

## Da hipótese ao cruzamento (conceito, sem prompt)

Uma hipótese vira uma pergunta, uma taxa por grupo e uma comparação. Exemplo da aula 1: perda mensal média em 2025, 9,0% no plano mensal contra 2,6% no anual. Três cuidados antes de acreditar numa diferença: (1) comparar coisas comparáveis (o anual só pode sair no aniversário); (2) olhar o tamanho de cada grupo; (3) desconfiar de diferenças que somem quando se abre por outra variável.

## O que levar da aula 2

1. A pasta e o arquivo de contexto são o primeiro artefato do grupo: o bruto nunca é editado.
2. O agente executa e o grupo confere: ler o código, rodar de novo e checar três números à mão.
3. Limpar é decidir e registrar: corrigir, remover ou marcar, com o motivo e o efeito em `decisoes.md`.
4. Média sem distribuição engana: em setembro de 2026, média de 83 minutos de treino por conta, mediana zero.
5. Cruzamento aponta suspeitos e não prova causa.

**Para a aula 3 (29/10):** trazer a base integrada no corte e o `decisoes.md`.
