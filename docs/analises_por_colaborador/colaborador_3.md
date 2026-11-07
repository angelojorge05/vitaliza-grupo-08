# Colaborador 3 · `uso_mensal.csv`: temporalidade, centro e correlação

Arquivos de dados: uso_mensal.csv.
Origem: `docs/roteiro_analises_exploratorias.md`. Análises: 6, 8, 10.

## Antes de começar
- Leia `CLAUDE.md` e `docs/contexto_case.md`. Nos prompts, troque `docs/dicionario_dados.md` por `docs/Vitaliza - Dicionário de dados.pdf` e `AGENTS.md` por `CLAUDE.md`.
- Todo pedido começa com "Mostre o plano antes de rodar" e termina com "Não altere nada em dados/brutos/". Aprove o plano antes da execução.
- Depois de cada resultado: leia o código, rode de novo, cheque três números à mão e compare com o dicionário.
- Mostre a contagem de linhas depois de cada filtro e de cada junção. Corte em 30/09/2026; horários em UTC (Z) convertidos para Brasília; contas @vitaliza.com.br não contam.
- Código em `src/` ou `notebooks/`; tabelas em `dados/processados/`; resultados em `saidas/`.
- Cada decisão de limpeza (corrigir, remover ou marcar) vai no `decisoes.md`, com o motivo e o efeito na contagem.

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

### Resultado e decisões (preencher)
- Contagens obtidas:
- Divergências em relação ao "Confira":
- Decisões para o `decisoes.md`:

---

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

### Resultado e decisões (preencher)
- Contagens obtidas:
- Divergências em relação ao "Confira":
- Decisões para o `decisoes.md`:

---

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

### Resultado e decisões (preencher)
- Contagens obtidas:
- Divergências em relação ao "Confira":
- Decisões para o `decisoes.md`:
