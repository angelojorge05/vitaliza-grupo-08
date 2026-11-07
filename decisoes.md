# Registro de decisões · Vitaliza grupo 08

Cada problema de dados tem três saídas: corrigir, remover ou marcar.
Toda escolha entra aqui com o motivo e o efeito na contagem.

| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |
|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|
| 1 | 07/11/2026 | assinaturas.csv + usuarios.csv | 60 contas de teste (e-mail @vitaliza.com.br; plano `cortesia`, canal `interno`) entre as ativas | remover | CLAUDE.md: contas de teste não contam | 14.813 → 14.753 pagantes ativos |
| 2 | 07/11/2026 | usuarios.csv | `sexo` com 6 grafias (F, Fem, feminino, M, Masc, masculino); 700 `sexo` vazios entre os pagantes | corrigir (substitui a coluna `sexo`; o original continua em dados/brutos/) | mesma categoria escrita de jeitos diferentes | 6 grafias → 2 valores (F 7.348, M 6.705); 700 vazios continuam vazios; 14.753 linhas |
| 3 | 07/11/2026 | usuarios.csv | `sistema` com 5 grafias (android, Android, ios, iOS, IOS) | corrigir (substitui a coluna `sistema`; o original continua em dados/brutos/) | maiúsculas diferentes da mesma categoria | 5 grafias → 2 valores (android 7.475, ios 7.278); 14.753 linhas |
| 4 | 07/11/2026 | usuarios.csv | `cidade` com abreviações e acentos (BH, BSB, Floripa, Rio, RJ, SP, Sampa, etc.) | corrigir (substitui a coluna `cidade`; o original continua em dados/brutos/) | mesma cidade escrita de jeitos diferentes; "RJ" e "SP" conferidos contra a `uf` (97 em RJ, 269 em SP) | 13 cidades nos pagantes; 14.753 linhas |
| 5 | 07/11/2026 | usuarios.csv | `data_nascimento` depois do corte ou antes de 1920 | marcar (`flag_nascimento_invalido`) | data impossível; não dá para corrigir e a idade pode ser útil depois | 133 marcados entre os pagantes; 14.753 linhas |
| 6 | 07/11/2026 | usuarios.csv | `data_cadastro` depois do corte | marcar (`flag_cadastro_apos_corte`) | contrariaria o corte | 0 marcados entre os pagantes; 14.753 linhas |
| 7 | 07/11/2026 | eventos_assinatura.csv | `data_hora` mistura UTC (com `Z`, 186.323 eventos) e horário sem fuso (89.242) | corrigir (converte para Brasília em `utils.para_brasilia`; sem `Z` já é Brasília, segundo o contexto do case) | CLAUDE.md: converter para Brasília antes de comparar; o dicionário em PDF ainda não foi lido | 21.951 eventos mudam de dia; 7.888 de 9.418 eventos das 2.250 contas ficam até 31/07 (Brasília) |
| 8 | 07/11/2026 | eventos_assinatura.csv + assinaturas.csv | 171 contas com início antes de 01/07/2024 não têm evento de início; 223 contas têm mais de um desligamento | marcar (`sem_evento_inicio`); vale o último evento de renovação até 31/07; sem desligamento, renovação ligada | o log só começa em 01/07/2024; o último evento define a situação | 171 marcadas (92 desligadas e 79 ligadas em 31/07); 2.250 linhas |
| 9 | 07/11/2026 | eventos_assinatura.csv | `cancelamento_web` pode ou não ser desligamento da renovação | marcar (testadas as duas versões; a principal não o conta) | o dicionário não deixa claro; o resultado não depende da escolha | idêntico nas duas: 1.427 desligadas, 754 ligadas, 69 não assinavam (soma 2.250) |
