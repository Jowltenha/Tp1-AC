# relatorios/ — convenções do subprojeto

> Nível 5 (subdiretório). Só o que é específico da automação de relatórios.

- Relatórios são **somente leitura**: nunca chamam `reservar`, `liberar` ou qualquer método que altere estado.
- Saída sempre em CSV UTF-8 com cabeçalho, gravada em `relatorios/saida/` (pasta ignorada pelo git).
- A semana do relatório começa na segunda-feira da data atual.
- Exemplo: `python3 relatorios/relatorio_ocupacao.py --saida relatorios/saida/ocupacao.csv`
