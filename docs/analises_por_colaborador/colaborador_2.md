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

### Resultado e decisões (07/11/2026, Felipe · execução Claude, `src/validade_atividades.py`)
- Contagens obtidas: 1.254.475 treinos; 679.640 com distância (54,2%); mediana 6,47 km; **951 acima de 200 km** (maior: 10.012,75 km, pedal de 160 min do `apple_health`); **3.649 com duração zero**, nenhum negativo. Por tipo (>200 km): corrida+run 555, caminhada+walk 269, pedal+ride 127; por origem: app 673, garmin 146, apple_health 132.
- Divergências em relação ao "Confira": **nenhuma** — todos os valores batem.
- Decisões para o `decisoes.md`: marcar os 951 (>200 km) como fisicamente impossíveis e os 3.649 (duração 0) como inválidos para agregados de engajamento; os 574.835 sem distância ficam como estão (ausência de GPS, não erro). Nada removido do bruto.

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

### Resultado e decisões (07/11/2026, Felipe · execução Claude, `src/consistencia_tipos.py`)
- Contagens obtidas: **11 valores para 7 tipos**; em inglês: run 162.108, walk 88.509, strength 85.548, ride 40.765 = **376.930 (30,0%)**, todos da origem `app`. Depois do mapa (run→corrida, walk→caminhada, ride→pedal, strength→forca): corrida 385.926, caminhada 206.533, forca 198.252, funcional 145.476, yoga 113.849, hiit 109.934, pedal 94.505.
- Divergências em relação ao "Confira": **nenhuma**.
- Decisões para o `decisoes.md`: corrigir (padronizar PT) **só em cópia processada**, nunca no bruto; mapa proposto acima, 376.930 linhas afetadas, 0 removidas. Toda contagem por tipo no projeto deve usar o tipo canônico (contar só `corrida` deixaria 162.108 de fora).

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

### Resultado e decisões (07/11/2026, Felipe · execução Claude, `src/unicidade_duplicados.py`)
- Contagens obtidas: candidatos (conta+tipo canônico+duração) 16.039 → com início ≤5 min já com o fuso do garmin corrigido (UTC−3h): **9.383 pares únicos = 5.199 garmin + 4.184 apple_health**; a distância é igual nos 9.383. Armadilha reproduzida: sem corrigir o fuso só aparecem os 4.184 do apple_health.
- Divergências em relação ao "Confira": **nenhuma**. Observação de método: o par exige o tipo na forma canônica (análise 4), porque o app grava 30% em inglês e o relógio em português.
- Decisões para o `decisoes.md`: marcar os 9.383 pares como o mesmo treino registrado duas vezes; em cópias processadas e agregados, manter 1 registro por par (proposta: o do relógio, que traz `fc_media`); efeito nos agregados: 1.254.475 → 1.245.092 treinos. Bruto intacto.
