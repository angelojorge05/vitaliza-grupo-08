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
