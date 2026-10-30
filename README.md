# Vitaliza · grupo 08

Projeto do MBA em IA e Dados para Negócios (Módulo 2, Trilha de Tecnologia).

## Sobre o projeto
A Vitaliza é um app brasileiro de assinatura (fictício) para quem treina: registro de treino com GPS, treinos em vídeo e rede social, com plano mensal e anual. Em 30/09/2026, data de corte da base, tinha 14.753 assinantes pagantes, mas o churn mensal subiu de 5,6% em 2025 para 6,6% em 2026 e a empresa não sabe explicar por quê.

Este projeto usa a base da Vitaliza para responder ao que a empresa não consegue sozinha: quem vai sair, em quem vale a pena agir, com qual mensagem e quanto isso rende. O trabalho percorre, ao longo do módulo, um sistema de cinco peças: dados, extração com IA generativa, previsão, decisão de contato e mensagem. Os objetivos vão da análise descritiva (contar e medir a base) e diagnóstica (explicar a subida de 2026) até a clusterização, a previsão de saída nos 60 dias seguintes ao corte, o cálculo do valor do contato dentro do orçamento de CRM de R$ 40.000 por mês e a escrita das mensagens.

Todo o processo segue o CRISP-DM, com as regras do grupo no CLAUDE.md e cada decisão de limpeza registrada no decisoes.md.

## Estrutura
- `CLAUDE.md`: regras do grupo, lidas pelo agente no início de cada sessão
- `decisoes.md`: registro de cada decisão de limpeza
- `docs/`: enunciado e dicionário de dados
- `dados/brutos/`: arquivos originais (só leitura, fora do git)
- `dados/processados/`: tabelas intermediárias (fora do git)
- `notebooks/`, `src/`: código
- `saidas/`: resultados, tabelas e gráficos

## Fluxo
1. Abrir a pasta no Claude Code.
2. Pedir o plano antes de executar; conferir o resultado.
3. Commit antes de cada pedido grande.
