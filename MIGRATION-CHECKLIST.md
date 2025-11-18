# ✅ Checklist de Migração: Railway → VPS Hostinger

Use este checklist para garantir que todos os passos da migração foram realizados corretamente.

## 📋 Fase 1: Preparação

### Antes de Começar
- [ ] Backup completo do banco de dados do Railway realizado
- [ ] Backup dos arquivos de mídia/mapas do Railway (se aplicável)
- [ ] Acesso SSH à VPS Hostinger configurado
- [ ] Domínio apontando para IP da VPS (ou DNS preparado)
- [ ] Informações de acesso ao banco de dados do Railway anotadas

## 📋 Fase 2: Setup da VPS

### Instalação de Dependências
- [ ] Sistema atualizado (`apt update && apt upgrade`)
- [ ] Python 3.11 instalado
- [ ] PostgreSQL instalado e rodando
- [ ] Nginx instalado
- [ ] Gunicorn instalado (via pip no venv)
- [ ] Git instalado
- [ ] Certbot instalado (para SSL)
- [ ] Firewall (UFW) configurado

### Configuração do PostgreSQL
- [ ] PostgreSQL rodando (`sudo systemctl status postgresql`)
- [ ] Usuário do banco de dados criado
- [ ] Banco de dados criado
- [ ] Permissões configuradas corretamente

### Backup Restaurado
- [ ] Backup do banco de dados restaurado na VPS
- [ ] Dados verificados (login, empresas, etc.)
- [ ] Migrações executadas (`python manage.py migrate`)

## 📋 Fase 3: Configuração da Aplicação

### Repositório e Código
- [ ] Repositório clonado em `/var/www/saas-viabilidade`
- [ ] Branch correto selecionado
- [ ] Última versão do código baixada

### Configuração de Ambiente
- [ ] Arquivo `.env` criado a partir de `.env.example.vps`
- [ ] `SECRET_KEY` gerada e configurada
- [ ] `DEBUG=False` configurado
- [ ] `ALLOWED_HOSTS` configurado com domínio correto
- [ ] `CSRF_TRUSTED_ORIGINS` configurado com HTTPS
- [ ] `DATABASE_URL` configurada corretamente
- [ ] Configurações de email configuradas

### Ambiente Virtual
- [ ] Ambiente virtual criado (`python3.11 -m venv venv`)
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Permissões do diretório corretas

### Arquivos Estáticos e Mídia
- [ ] `collectstatic` executado
- [ ] Diretório `staticfiles` criado e populado
- [ ] Diretório `media` criado com permissões corretas
- [ ] Diretórios de mapas criados (`Mapas/kml`, `Mapas/kmz`, etc.)

## 📋 Fase 4: Configuração do Gunicorn

### Service Systemd
- [ ] Arquivo `gunicorn.service` copiado para `/etc/systemd/system/`
- [ ] Usuário e grupo ajustados no arquivo service
- [ ] Caminhos ajustados no arquivo service
- [ ] `EnvironmentFile` apontando para `.env`
- [ ] `systemctl daemon-reload` executado
- [ ] Serviço habilitado (`systemctl enable gunicorn`)
- [ ] Serviço iniciado (`systemctl start gunicorn`)
- [ ] Status verificado (`systemctl status gunicorn`)

### Configuração
- [ ] Arquivo `gunicorn_config.py` no diretório raiz
- [ ] Configurações ajustadas (workers, timeout, etc.)
- [ ] Diretório de logs criado (`/var/log/gunicorn`)
- [ ] Permissões de logs configuradas

### Testes
- [ ] Gunicorn respondendo em `http://127.0.0.1:8000`
- [ ] Logs sendo gerados corretamente
- [ ] Sem erros nos logs

## 📋 Fase 5: Configuração do Nginx

### Configuração do Site
- [ ] Arquivo `nginx.conf` copiado para `/etc/nginx/sites-available/saas-viabilidade`
- [ ] `server_name` ajustado com domínio correto
- [ ] Caminhos de arquivos estáticos corretos
- [ ] Caminhos de arquivos de mídia corretos
- [ ] Proxy configurado para `127.0.0.1:8000`
- [ ] Link simbólico criado em `/etc/nginx/sites-enabled/`

### Testes
- [ ] Configuração testada (`nginx -t`)
- [ ] Nginx reiniciado (`systemctl restart nginx`)
- [ ] Status verificado (`systemctl status nginx`)
- [ ] Site acessível via HTTP

## 📋 Fase 6: SSL/HTTPS

### Certificado Let's Encrypt
- [ ] Certbot instalado
- [ ] Certificado SSL obtido (`certbot --nginx`)
- [ ] Redirecionamento HTTP → HTTPS configurado
- [ ] Renovação automática configurada
- [ ] Certificado testado (acesso via HTTPS)

### Testes
- [ ] Site acessível via HTTPS
- [ ] Certificado válido (sem avisos no navegador)
- [ ] Redirecionamento HTTP → HTTPS funcionando

## 📋 Fase 7: Testes Finais

### Funcionalidades
- [ ] Login RM funcionando
- [ ] Login empresa funcionando
- [ ] Dashboard acessível
- [ ] Upload de arquivos funcionando
- [ ] Verificação de viabilidade funcionando
- [ ] Sistema de tickets funcionando
- [ ] Emails sendo enviados

### Performance
- [ ] Tempo de carregamento aceitável
- [ ] Arquivos estáticos carregando corretamente
- [ ] Sem erros 404 ou 500

### Logs
- [ ] Sem erros críticos nos logs do Gunicorn
- [ ] Sem erros críticos nos logs do Nginx
- [ ] Logs de acesso sendo gerados

## 📋 Fase 8: Manutenção e Monitoramento

### Backups
- [ ] Script de backup criado (`backup-db.sh`)
- [ ] Backup automático configurado no crontab
- [ ] Backup manual testado
- [ ] Estratégia de retenção configurada

### Monitoramento
- [ ] Logs sendo monitorados
- [ ] Alertas configurados (se aplicável)
- [ ] Processo de verificação periódica definido

### Documentação
- [ ] Informações de acesso documentadas
- [ ] Procedimentos de manutenção documentados
- [ ] Contatos de suporte atualizados

## 📋 Fase 9: Finalização

### Desativação do Railway
- [ ] Migração completamente testada e funcionando
- [ ] Período de observação concluído (recomendado 24-48h)
- [ ] Backups finais do Railway realizados
- [ ] Railway desativado/pausado
- [ ] DNS atualizado (se necessário)

### Documentação Final
- [ ] Informações da VPS documentadas
- [ ] Credenciais seguras armazenadas
- [ ] Documentação atualizada
- [ ] Equipe notificada da migração

## 🆘 Problemas Encontrados

Use esta seção para anotar problemas encontrados durante a migração:

- [ ] Problema: _____________________
  - Solução: _____________________
  
- [ ] Problema: _____________________
  - Solução: _____________________

## ✅ Finalização

- [ ] Todas as fases concluídas
- [ ] Sistema funcionando 100%
- [ ] Documentação atualizada
- [ ] Equipe treinada (se necessário)
- [ ] Migração concluída com sucesso! 🎉

---

**Data da Migração:** _____________

**Responsável:** _____________

**Observações Finais:**

_________________________________
_________________________________
_________________________________

