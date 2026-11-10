# Completude e duplicatas do usuarios.csv

Código: `src/completude_usuarios.py`. Leitura em texto puro; só leitura (SHA-256 igual antes e depois).

## Linhas e duplicatas

- Linhas: **64.948** (dicionário: 64.948); `user_id` únicos: 64.948.
- Duplicadas: `user_id` **0**, e-mail (sem diferenciar caixa) **959**, linha inteira **0**.

## Vazios por coluna (da mais vazia para a menos vazia)

| Coluna | Nulos | Só espaço | Vazios | % | Ausência permitida pelo dicionário |
|---|---:|---:|---:|---:|---|
| `data_nascimento` | 3.301 | 0 | 3.301 | 5,1% | não indicada |
| `sexo` | 3.142 | 0 | 3.142 | 4,8% | não indicada |
| `cep_prefixo` | 1.894 | 0 | 1.894 | 2,9% | não indicada |
| `canal_aquisicao` | 0 | 0 | 0 | 0,0% | não indicada |
| `cidade` | 0 | 0 | 0 | 0,0% | não indicada |
| `data_cadastro` | 0 | 0 | 0 | 0,0% | não indicada |
| `email` | 0 | 0 | 0 | 0,0% | não indicada |
| `relogio_conectado` | 0 | 0 | 0 | 0,0% | sim ("se houver") |
| `sistema` | 0 | 0 | 0 | 0,0% | não indicada |
| `uf` | 0 | 0 | 0 | 0,0% | não indicada |
| `user_id` | 0 | 0 | 0 | 0,0% | não indicada |
| `versao_app` | 0 | 0 | 0 | 0,0% | não indicada |

Em cada coluna, nulos + só espaço = vazios. Linhas: 64.948 antes e depois.

## Completude

- Células preenchidas (todas as colunas): **98,9%**.
- Sem contar `relogio_conectado` (que não tem vazios): **98,8%**.
- Contas sem nenhum vazio nas outras 11 colunas: 56.968 (87,7%).

## E-mail repetido (possível pessoa em duas contas)

- Nenhum e-mail se repete no texto bruto, mas **959 e-mails** aparecem em duas contas depois de ignorar maiúsculas e minúsculas (**1.918 contas**, 2 por e-mail), por exemplo `aline.campos28@gmail.com` e `ALINE.CAMPOS28@GMAIL.COM`.
- Em 959 desses e-mails as duas contas têm a mesma data de nascimento, sexo e cidade; as datas de cadastro são diferentes.
- 472 dessas contas têm assinatura em `assinaturas.csv`; nenhuma é conta de teste.
- **Não removi nem juntei nada.** Cada `user_id` tem o seu onboarding, assinaturas e treinos; juntar contas exige uma regra que o dicionário não dá. Proposta: **marcar** (`flag_email_repetido`) e decidir depois, com o grupo, se as duas contas contam como uma pessoa.

## O que o dicionário não diz

- Nenhuma coluna de `usuarios.csv` é marcada como opcional. `relogio_conectado` admite ausência ("se houver"), mas não tem nenhum vazio: a ausência vem escrita como `nenhum` (40.159 contas), contra 13.403 `garmin` e 11.386 `apple_watch`.
- O dicionário afirma que os campos digitados pela pessoa (`data_nascimento`, `sexo`, `cidade`, `uf`, `cep_prefixo`) não passam por validação, mas não diz se podem ficar em branco. Por isso os vazios dessas colunas ficam como **lacuna a decidir**, e não como problema confirmado.
- Os valores impossíveis (datas fora do corte) e as grafias de `sexo`, `sistema` e `cidade` já foram tratados para os pagantes nas decisões 2 a 6. Este relatório cobre as 64.948 contas só quanto a vazios e duplicatas.
