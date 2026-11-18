# scripts/migracao/ — convenções do subprojeto

> Nível 5 (subdiretório). Só o que é específico dos scripts de migração.

- Todo script é **dry-run por padrão**. Gravar de fato exige a flag `--aplicar`, que só um humano executa.
  Ao testar, rode sempre sem `--aplicar`.
- Arquivos do legado: CSV com separador `;` e encoding `latin-1`. Colunas em maiúsculas (`NOME;CPF;EMAIL;FONE`).
- Normalize na entrada: e-mail em minúsculas, CPF só com dígitos (feito por `RepositorioPacientes.cadastrar`).
- Linha inválida não interrompe a migração: é contada em `rejeitados` e logada em `stderr` com o número da linha.
- Todo script termina imprimindo um resumo `[DRY-RUN]` ou `[APLICADO]` com contagens `lidos/migrados/rejeitados`.
- Use `exemplo_legado.csv` para testes manuais; nunca commite CSVs reais do legado (contêm dados pessoais).
- Exemplo: `python3 scripts/migracao/migrar_pacientes_legado.py scripts/migracao/exemplo_legado.csv`
