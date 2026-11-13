# MANU GitHub Actions — simulação agendada
O workflow `.github/workflows/paper-simulation.yml` tenta rodar a cada 15 minutos e permite execução manual.
**Não é tempo real**: o GitHub pode atrasar ou pular agendamentos. Nenhuma operação é feita na Binance.
Ele usa exclusivamente endpoints públicos de candles Spot e USDTBRL; não possui API key ou endpoint de ordens.
Cada execução registra o estado em `paper_state.json` e preserva posições simuladas entre execuções.
Se um feed falhar, a execução falha sem publicar novo estado. Isso NÃO equivale a stop-loss real; gaps e indisponibilidade podem gerar perdas simuladas acima dos limites.
O controle de perda diária ainda é simplificado (realizado) e não está pronto para operações reais.
Verifique Actions → MANU Paper Simulation → Run workflow; a execução e a autorização de gravação dependem das configurações do GitHub.
O arquivo JSON é público. Não coloque segredos, credenciais ou dados pessoais nele.
