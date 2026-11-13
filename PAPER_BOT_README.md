# MANU Trading Bot V3 — Paper Mode
Serviço experimental de análise contínua com **dados públicos Binance Spot**. Não acessa carteira, não utiliza chaves, não envia ordens.

## Executar
Requer Python 3.10+ e conexão à internet.
```bash
python3 paper_bot.py
```
O histórico fica em `manu_paper.sqlite3` (não publicar no GitHub).

## Limitações
- O GitHub Pages hospeda apenas o painel estático e **não executa** este Python em segundo plano.
- Para funcionar continuamente é necessário executar em máquina/servidor sempre ligado; esta versão ainda não foi implantada nem validada em produção.
- Preços públicos Binance podem ter restrições regionais, indisponibilidade e latência. O código usa polling de 60 segundos, **não WebSocket em tempo real**.
- Simulação de preenchimento é simplificada: não modela livro de ofertas, execução parcial, gaps, câmbio variável no fechamento, tributos nem limites reais de ordem.
- Limite diário de R$ 2 é baseado em P&L **realizado** e não impede perdas maiores por posições abertas ou gaps. Não é proteção garantida.
- Estratégia de cruzamento de médias é experimental; sem backtest robusto ou expectativa positiva demonstrada.
- Sem alavancagem, sem futuros, sem negociação real. **Não adicione chaves de API a este repositório público.**

## Próximas validações
Backtest histórico com custos, reconciliação de saldo, P&L marcado a mercado, limites de perda incluindo posições abertas, filtros de liquidez, segurança, testes de falha, monitoramento e implantação privada antes de qualquer hipótese de negociação real.
