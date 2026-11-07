# Análise 12 · prática principal (em grupo)

Origem: `docs/roteiro_analises_exploratorias.md`. Faça depois que as análises individuais estiverem conferidas.

## Antes de começar
- Leia `CLAUDE.md` e `docs/contexto_case.md`. Nos prompts, troque `docs/dicionario_dados.md` por `docs/Vitaliza - Dicionário de dados.pdf` e `AGENTS.md` por `CLAUDE.md`.
- Todo pedido começa com "Mostre o plano antes de rodar" e termina com "Não altere nada em dados/brutos/". Aprove o plano antes da execução.
- Depois de cada resultado: leia o código, rode de novo, cheque três números à mão e compare com o dicionário.
- Mostre a contagem de linhas depois de cada filtro e de cada junção. Corte em 30/09/2026; horários em UTC (Z) convertidos para Brasília; contas @vitaliza.com.br não contam.
- Código em `src/` ou `notebooks/`; tabelas em `dados/processados/`; resultados em `saidas/`.
- Cada decisão de limpeza (corrigir, remover ou marcar) vai no `decisoes.md`, com o motivo e o efeito na contagem.

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
