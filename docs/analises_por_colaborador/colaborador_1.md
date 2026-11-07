# Colaborador 1 · Grupos, junções e vazamento

Arquivos de dados: assinaturas.csv, usuarios.csv, eventos_assinatura.csv, atividades.parquet.
Origem: `docs/roteiro_analises_exploratorias.md`. Análises: 1, 7, 11.

## Antes de começar
- Leia `CLAUDE.md` e `docs/contexto_case.md`. Nos prompts, troque `docs/dicionario_dados.md` por `docs/Vitaliza - Dicionário de dados.pdf` e `AGENTS.md` por `CLAUDE.md`.
- Todo pedido começa com "Mostre o plano antes de rodar" e termina com "Não altere nada em dados/brutos/". Aprove o plano antes da execução.
- Depois de cada resultado: leia o código, rode de novo, cheque três números à mão e compare com o dicionário.
- Mostre a contagem de linhas depois de cada filtro e de cada junção. Corte em 30/09/2026; horários em UTC (Z) convertidos para Brasília; contas @vitaliza.com.br não contam.
- Código em `src/` ou `notebooks/`; tabelas em `dados/processados/`; resultados em `saidas/`.
- Cada decisão de limpeza (corrigir, remover ou marcar) vai no `decisoes.md`, com o motivo e o efeito na contagem.

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

### Resultado e decisões (preencher)
- Contagens obtidas:
- Divergências em relação ao "Confira":
- Decisões para o `decisoes.md`:

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

### Resultado e decisões (preencher)
- Contagens obtidas:
- Divergências em relação ao "Confira":
- Decisões para o `decisoes.md`:

---

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

### Resultado e decisões
- Contagens obtidas: 32.643 → 14.813 ativas → 2.310 com renovação `nao` → 2.250 sem contas de teste. Em 31/07: 1.427 desligadas, 754 ligadas, 69 ainda não assinavam. O retrato erra 823 (36,6%). Detalhes em `saidas/vazamento_renovacao_31jul.md`.
- Divergências em relação ao "Confira": nenhuma.
- Decisões para o `decisoes.md`: 13 (fuso), 14 (início antes de 01/07/2024 e último evento) e 15 (`cancelamento_web`, sem efeito na contagem).
