# Colaborador 2 · Qualidade de `atividades.parquet`

Arquivos de dados: atividades.parquet.
Origem: `docs/roteiro_analises_exploratorias.md`. Análises: 3, 4, 5.

## Antes de começar
- Leia `CLAUDE.md` e `docs/contexto_case.md`. Nos prompts, troque `docs/dicionario_dados.md` por `docs/Vitaliza - Dicionário de dados.pdf` e `AGENTS.md` por `CLAUDE.md`.
- Todo pedido começa com "Mostre o plano antes de rodar" e termina com "Não altere nada em dados/brutos/". Aprove o plano antes da execução.
- Depois de cada resultado: leia o código, rode de novo, cheque três números à mão e compare com o dicionário.
- Mostre a contagem de linhas depois de cada filtro e de cada junção. Corte em 30/09/2026; horários em UTC (Z) convertidos para Brasília; contas @vitaliza.com.br não contam.
- Código em `src/` ou `notebooks/`; tabelas em `dados/processados/`; resultados em `saidas/`.
- Cada decisão de limpeza (corrigir, remover ou marcar) vai no `decisoes.md`, com o motivo e o efeito na contagem.

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

### Resultado e decisões (preencher)
- Contagens obtidas:
- Divergências em relação ao "Confira":
- Decisões para o `decisoes.md`:

---

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

### Resultado e decisões (preencher)
- Contagens obtidas:
- Divergências em relação ao "Confira":
- Decisões para o `decisoes.md`:

---

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

### Resultado e decisões (preencher)
- Contagens obtidas:
- Divergências em relação ao "Confira":
- Decisões para o `decisoes.md`:
