# Teste da 3ª variável — saiu × ficou (passo 5 da prática 12)

Gerado por `src/terceira_variavel.py` a partir de `comportamento_ate_30jun.parquet` (14.059 pagantes ativos em 30/06; tudo medido até 30/06).

## Churn do trimestre por recorte

### Plano

| plano_atual   |    n |   churn_pct |
|:--------------|-----:|------------:|
| anual         | 8212 |        10.9 |
| mensal        | 5847 |        24.7 |

### Tempo de casa em 30/06

| faixa_casa   |    n |   churn_pct |
|:-------------|-----:|------------:|
| até 6m       | 5421 |        16.4 |
| 6–12m        | 3467 |        25   |
| 1–2a         | 3540 |        12.3 |
| 2a+          | 1605 |         8.9 |

### Canal de cobrança

| canal_cobranca   |    n |   churn_pct |
|:-----------------|-----:|------------:|
| app_store        | 5061 |        14.6 |
| google_play      | 4769 |        17.5 |
| web_cartao       | 2862 |        18.3 |
| web_pix          | 1367 |        18.2 |

## O gap de engajamento sobrevive ao controle?

Mediana de treinos jan–jun (saiu × ficou) **dentro de cada plano**:

| plano_atual   |   ficou |   saiu |   gap |
|:--------------|--------:|-------:|------:|
| anual         |      42 |      9 |   -33 |
| mensal        |      47 |     40 |    -7 |

Dentro de cada **faixa de tempo de casa**:

| faixa_casa   |   ficou |   saiu |   gap |
|:-------------|--------:|-------:|------:|
| até 6m       |      31 |     29 |    -2 |
| 6–12m        |      53 |     31 |   -22 |
| 1–2a         |      52 |     37 |   -15 |
| 2a+          |      53 |     20 |   -33 |

Sessões no app/mês dentro de cada plano:

| plano_atual   |   ficou |   saiu |   gap |
|:--------------|--------:|-------:|------:|
| anual         |       8 |    2.8 |  -5.2 |
| mensal        |      10 |    8.7 |  -1.3 |

## Leitura

1. **Plano é a 3ª variável mais forte do churn**: mensal sai a 24,7%, anual a 10,9% (e o grupo que saiu é 62% mensal; o que ficou, 62% anual).
2. **Mas o gap de engajamento NÃO é só composição** — ele sobrevive ao controle e muda de cara: no plano **anual**, quem saiu treinou 9 contra 42 de quem ficou (gap −33) — abandono de uso meses antes de deixar a assinatura expirar. No **mensal**, o gap é pequeno (40 × 47): o churner mensal ainda treinava quase como quem ficou.
3. **Tempo de casa**: o churn concentra-se em 6–12 meses (25,0%) — a janela da primeira renovação anual — e cai com a antiguidade (2a+: 8,9%). Entre novatos (até 6m) o gap de treino é quase nulo (−2); entre veteranos que saem, é enorme (−33).
4. **Implicação**: engajamento em queda é um ótimo preditor para o churn do plano anual (dá tempo de agir antes da renovação), mas fraco para o mensal — onde a saída deve ter outros motores (preço, cobrança/recusas, concorrência). A régua de retenção não pode ser uma só.

As 3 frases finais (diz / não diz / próxima pergunta) ficam para a discussão em grupo.
