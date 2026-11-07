# Colaborador 4 · Distribuições e conferência das análises já feitas

Arquivos de dados: atividades.parquet (análise 9).
Origem: `docs/roteiro_analises_exploratorias.md`. Análises: 0, 2, 9.

## Antes de começar
- Leia `CLAUDE.md` e `docs/contexto_case.md`. Nos prompts, troque `docs/dicionario_dados.md` por `docs/Vitaliza - Dicionário de dados.pdf` e `AGENTS.md` por `CLAUDE.md`.
- Todo pedido começa com "Mostre o plano antes de rodar" e termina com "Não altere nada em dados/brutos/". Aprove o plano antes da execução.
- Depois de cada resultado: leia o código, rode de novo, cheque três números à mão e compare com o dicionário.
- Mostre a contagem de linhas depois de cada filtro e de cada junção. Corte em 30/09/2026; horários em UTC (Z) convertidos para Brasília; contas @vitaliza.com.br não contam.
- Código em `src/` ou `notebooks/`; tabelas em `dados/processados/`; resultados em `saidas/`.
- Cada decisão de limpeza (corrigir, remover ou marcar) vai no `decisoes.md`, com o motivo e o efeito na contagem.

## Já feitas: conferir
As análises 0 (`saidas/inventario.md`, `src/inventario.py`) e 2 (`src/vazios_onboarding.py`) já têm código. Rode de novo, compare com os valores de "Confira" abaixo e registre divergências.

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

### Resultado e decisões (preencher)
- Contagens obtidas:
- Divergências em relação ao "Confira":
- Decisões para o `decisoes.md`:

---

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

### Resultado e decisões (preencher)
- Contagens obtidas:
- Divergências em relação ao "Confira":
- Decisões para o `decisoes.md`:

---

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

### Resultado e decisões (preencher)
- Contagens obtidas:
- Divergências em relação ao "Confira":
- Decisões para o `decisoes.md`:
