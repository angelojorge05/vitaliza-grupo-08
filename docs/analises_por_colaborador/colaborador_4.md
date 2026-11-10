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

### Resultado e decisões (07/11/2026, Felipe · execução Claude)
- Contagens obtidas: `src/inventario.py` reexecutado sem alteração; para os 12 arquivos tabulares a saída é **idêntica** ao `saidas/inventario.md` commitado (diff vazio fora do carimbo de data) — mesmas linhas, células faltantes e as 8 divergências consolidadas. Conferência manual: `wc -l usuarios.csv` = 64.949 (64.948 + cabeçalho); parquet = 1.254.475 (pyarrow); 60 linhas `plano_atual=cortesia` = 60 `canal_cobranca=interno`. Integridade: "OK, nada alterado".
- Divergências em relação ao "Confira": nenhuma nos tabulares. **Ressalva:** as duas entradas de heatmaps (ZIPs de 12.426 e 13.047 PNGs) não foram conferidas nesta rodada — os ZIPs não estavam no disco local; o `inventario.md` do repositório foi mantido como está.
- Decisões para o `decisoes.md`: nenhuma nova (o inventário só marca; as divergências já estão listadas nele).

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

### Resultado e decisões (07/11/2026, Felipe · execução Claude)
- Contagens obtidas: `src/vazios_onboarding.py` reexecutado: 63.929 linhas = 63.929 user_id únicos, 0 repetidos; `objetivo_texto` **5.467 vazias (8,6%)**, todas nulas, nenhuma só com espaços; `como_conheceu` 4.586 (7,2%); `nivel` **4.513 (7,1%)**; `dias_por_semana` **6.368 (10,0%)**. Conferência manual independente (pandas direto): 63.929 / 5.467 / 4.513 / 6.368 — idêntico. Achado adicional do script: o marcador `-` aparece 1.322× em `objetivo_texto` e 1.190× em `como_conheceu` (não contado como vazio).
- Divergências em relação ao "Confira": **nenhuma**; armadilha confirmada (`nivel` e `dias_por_semana` têm vazios e o dicionário não os marca como opcionais).
- Decisões para o `decisoes.md`: marcar vazios de `objetivo_texto`/`como_conheceu` como "sem resposta" (opcionais por desenho), incluindo o traço `-`; marcar vazios de `nivel` e `dias_por_semana` como categoria "não informado" para a modelagem. 0 linhas removidas.

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

### Resultado e decisões (07/11/2026, Felipe · execução Claude, `src/distribuicao_distancias.py`)
- Contagens obtidas: **679.640** treinos com distância; 45,9% na classe 5–10 km (30,6% em 0–5); Q1 **4,58** · mediana **6,47** · Q3 **9,58** · IQR **5,00**. Regra Q3+1,5×IQR (>17,08 km): **81.775** marcados, sendo **73.120 de pedal** (com `ride`), 8.355 corrida, 300 caminhada. Regra |z|>3 (>191,60 km; média 11,15, dp 60,15): **956** marcados (555 corrida, 274 caminhada, 127 pedal). Saídas: `saidas/distribuicao_distancias.md` e `.png`.
- Divergências em relação ao "Confira": **nenhuma**.
- Decisões para o `decisoes.md`: as duas regras **marcam**, nada é removido. Proposta: excluir dos agregados/correlações apenas os fisicamente impossíveis (>200 km, análise 3 — os 555 de corrida são os que derrubam o r de 0,88 para 0,12); os 81.775 do IQR são longos porém plausíveis e permanecem.
