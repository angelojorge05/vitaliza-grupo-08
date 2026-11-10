# Base única · pagantes em 30/06 com rótulo saiu/ficou

Gerada por `src/base_unica.py`: **14.059 assinantes × 39 variáveis**, tudo medido até 30/06/2026 (anti-vazamento); rótulo = fim de assinatura em jul–set. Insumo para o K-means de personas e para a modelagem de churn. O arquivo fica em `dados/processados/` (fora do Git): regenerar com `python src/comportamento_usuarios.py` e depois `python src/base_unica.py`.

| Bloco | Variáveis |
|---|---|
| Identificação e rótulo | `user_id`, `grupo`, `plano_atual`, `canal_cobranca`, `inicio`, `data_fim` |
| Engajamento (treinos tratados) | `treinos_jan_jun`, `minutos_jan_jun`, `treinos_30d`, `treinos_60d`, `treinos_90d`, `recencia_dias`, `n_modalidades`, `pct_relogio`, `tendencia`, `sem_treino_jan_jun` |
| App (uso_mensal 2026) | `sessoes_app_mes`, `dias_ativos_mes`, `minutos_mes` |
| Perfil (usuarios) | `idade`, `flag_nascimento_invalido`, `sexo`, `uf`, `canal_aquisicao`, `sistema`, `relogio_conectado` |
| Onboarding | `nivel_declarado`, `dias_semana_declarado`, `como_conheceu` |
| Pagamentos (dedup, até 30/06) | `pg_aprovados`, `pg_recusas`, `pg_pct_recusa`, `pg_valor_medio`, `pg_metodo_principal` |
| Social | `n_seguindo`, `n_seguidores`, `n_posts` |
| Suporte | `n_tickets`, `ticket_categoria_principal` |

Regras aplicadas: duplicatas funcionais de pagamentos removidas (chave user_id + data/hora Brasília + valor + método + status + tentativa, só aprovados); vazios de contagem = 0; recência sem treino = 181 + flag; tendência sem base = 1,0; categóricas vazias = `nao_informado`; idade NA quando nascimento inválido (com flag).
