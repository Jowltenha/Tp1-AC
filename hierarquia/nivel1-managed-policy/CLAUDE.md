# Política gerenciada da organização (Managed policy)

> Nível 1. Instalar em `/etc/claude-code/CLAUDE.md` (Linux/WSL), `/Library/Application Support/ClaudeCode/CLAUDE.md`
> (macOS) ou `C:\Program Files\ClaudeCode\CLAUDE.md` (Windows). Mantido pela TI/segurança; o desenvolvedor não edita.

- Dados de pacientes são dados pessoais sensíveis (LGPD). Nunca copie dados reais de pacientes para prompts,
  arquivos de teste, logs ou commits; use dados fictícios.
- Nunca execute comandos contra bancos ou serviços de produção. Migrações e deploys em produção são
  executados apenas por humanos, pelo pipeline oficial.
- Não adicione dependências de terceiros sem aprovação registrada no PR.
