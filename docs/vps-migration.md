# Guia de Migração: Railway → VPS Hostinger

Este guia detalha o processo completo de migração do sistema SaaS Verificador de Viabilidade do Railway para uma VPS da Hostinger.

## 📋 Pré-requisitos

- Acesso SSH à VPS Hostinger (com permissões de root/sudo)
- Domínio configurado apontando para o IP da VPS
- Backup completo do banco de dados atual
- Acesso ao repositório Git do projeto

## 🚀 Passo a Passo

### 1. Preparação da VPS

#### 1.1. Conectar na VPS via SSH
```bash
ssh root@seu-ip-vps
# ou
ssh usuario@seu-ip-vps
```

#### 1.2. Executar o script de setup inicial
```bash
# Fazer upload do arquivo setup_vps.sh para a VPS
chmod +x setup_vps.sh
sudo ./setup_vps.sh
```

Este script irá:
- Atualizar o sistema
- Instalar Python 3.11, PostgreSQL, Nginx, Gunicorn e dependências
- Configurar o PostgreSQL e criar banco de dados
- Configurar firewall (UFW)
- Criar usuário para aplicação
- Criar estrutura de diretórios

**Importante:** Anote as informações do banco de dados exibidas ao final do script.

### 2. Migração do Banco de Dados

#### 2.1. Backup do banco de dados no Railway
```bash
# No seu ambiente local ou Railway, fazer backup:
pg_dump "DATABASE_URL_DO_RAILWAY" > backup.sql
```

#### 2.2. Restaurar backup na VPS
```bash
# Na VPS, restaurar o backup:
psql -h localhost -U usuario_banco -d nome_banco < backup.sql
```

Ou usando DATABASE_URL:
```bash
psql "DATABASE_URL_DA_VPS" < backup.sql
```

### 3. Configuração da Aplicação

#### 3.1. Clonar repositório
```bash
# Como usuário da aplicação (appuser)
sudo su - appuser
cd /var/www
git clone https://github.com/seu-usuario/Saas-Verificador-de-Viabilidade.git saas-viabilidade
cd saas-viabilidade
```

#### 3.2. Configurar arquivo .env
```bash
# Opção 1: Usar script automatizado (recomendado)
bash setup-env.sh

# Opção 2: Criar manualmente
cp .env.example.vps .env
nano .env
```

**Nota:** O script `setup-env.sh` cria o arquivo `.env` automaticamente e gera a `SECRET_KEY`. Depois, você só precisa editar as demais variáveis. Veja mais detalhes em `docs/vps-env-setup.md`.

Configure as seguintes variáveis:
```env
SECRET_KEY=sua-chave-secreta-forte-aqui
DEBUG=False
IS_LOCAL_DEV=False

ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com,127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com

DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_banco
DB_CONN_MAX_AGE=600

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
DEFAULT_FROM_EMAIL=seu-email@gmail.com
```

**Gerar SECRET_KEY:**
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

#### 3.3. Configurar permissões
```bash
chown -R appuser:appuser /var/www/saas-viabilidade
chmod +x deploy_vps.sh
```

### 4. Configuração do Gunicorn

#### 4.1. Instalar serviço systemd
```bash
sudo cp gunicorn.service /etc/systemd/system/
sudo nano /etc/systemd/system/gunicorn.service
```

Ajuste o usuário e caminhos no arquivo se necessário:
```
User=appuser
Group=appuser
WorkingDirectory=/var/www/saas-viabilidade
EnvironmentFile=/var/www/saas-viabilidade/.env
```

#### 4.2. Habilitar e iniciar serviço
```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn
```

### 5. Configuração do Nginx

#### 5.1. Copiar configuração do Nginx
```bash
sudo cp nginx.conf /etc/nginx/sites-available/saas-viabilidade
sudo nano /etc/nginx/sites-available/saas-viabilidade
```

Ajuste o `server_name` e outras configurações conforme necessário:
```
server_name seu-dominio.com www.seu-dominio.com;
```

#### 5.2. Habilitar site e testar
```bash
sudo ln -s /etc/nginx/sites-available/saas-viabilidade /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Configurar SSL (Let's Encrypt)

#### 6.1. Instalar certificado SSL
```bash
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

#### 6.2. Configurar renovação automática
```bash
# Verificar se o timer está ativo
sudo systemctl status certbot.timer
```

A renovação automática já está configurada por padrão.

#### 6.3. Atualizar configuração do Nginx
Após instalar o SSL, o Certbot atualizará automaticamente o `nginx.conf`. Verifique se a configuração está correta.

### 7. Primeiro Deploy

#### 7.1. Executar script de deploy
```bash
cd /var/www/saas-viabilidade
sudo -u appuser ./deploy_vps.sh
```

Este script irá:
- Ativar ambiente virtual
- Instalar/atualizar dependências
- Executar migrações
- Coletar arquivos estáticos
- Reiniciar serviços

#### 7.2. Criar superusuário (se necessário)
```bash
sudo -u appuser /var/www/saas-viabilidade/venv/bin/python manage.py createsuperuser
```

### 8. Verificação e Testes

#### 8.1. Verificar logs
```bash
# Logs do Gunicorn
sudo journalctl -u gunicorn -f

# Logs do Nginx
sudo tail -f /var/log/nginx/saas-viabilidade-error.log
sudo tail -f /var/log/nginx/saas-viabilidade-access.log

# Logs específicos do Gunicorn
sudo tail -f /var/log/gunicorn/error.log
```

#### 8.2. Testar aplicação
1. Acesse `https://seu-dominio.com`
2. Teste login
3. Teste upload de arquivos
4. Teste funcionalidades principais

#### 8.3. Verificar status dos serviços
```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql
```

### 9. Manutenção Contínua

#### 9.1. Deploy de atualizações
Sempre que houver atualizações no código:
```bash
cd /var/www/saas-viabilidade
sudo -u appuser git pull
sudo -u appuser ./deploy_vps.sh
```

#### 9.2. Backup regular
Configure backups automáticos do banco de dados:

```bash
# Criar script de backup
sudo nano /usr/local/bin/backup-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/saas-viabilidade"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump "DATABASE_URL" | gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

```bash
chmod +x /usr/local/bin/backup-db.sh

# Adicionar ao crontab
sudo crontab -e
# Adicionar linha:
0 2 * * * /usr/local/bin/backup-db.sh
```

## 🔧 Troubleshooting

### Erro: "Permission denied" em arquivos estáticos
```bash
sudo chown -R appuser:appuser /var/www/saas-viabilidade
sudo chmod -R 755 /var/www/saas-viabilidade
```

### Erro: Gunicorn não inicia
```bash
# Verificar logs
sudo journalctl -u gunicorn -n 50

# Verificar permissões
ls -la /var/www/saas-viabilidade

# Verificar arquivo .env
sudo -u appuser cat /var/www/saas-viabilidade/.env
```

### Erro: "502 Bad Gateway"
```bash
# Verificar se Gunicorn está rodando
sudo systemctl status gunicorn

# Verificar conexão
curl http://127.0.0.1:8000

# Reiniciar serviços
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### Erro: "Database connection failed"
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão
sudo -u postgres psql -c "\l"

# Verificar DATABASE_URL no .env
sudo -u appuser cat /var/www/saas-viabilidade/.env | grep DATABASE_URL
```

### Arquivos estáticos não carregam
```bash
# Recoletar arquivos estáticos
cd /var/www/saas-viabilidade
sudo -u appuser venv/bin/python manage.py collectstatic --noinput --clear

# Verificar permissões
sudo chown -R appuser:appuser /var/www/saas-viabilidade/staticfiles
```

## 📝 Checklist Final

- [ ] Banco de dados migrado e testado
- [ ] Aplicação configurada e rodando
- [ ] SSL/HTTPS configurado
- [ ] Serviços systemd configurados e ativos
- [ ] Logs funcionando corretamente
- [ ] Backups automáticos configurados
- [ ] Testes de todas as funcionalidades realizados
- [ ] Domínio apontando corretamente para VPS
- [ ] Firewall configurado corretamente

## 🔐 Segurança

1. **Atualizar sistema regularmente:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Manter backup atualizado:**
   - Configure backups automáticos diários
   - Teste restauração de backups periodicamente

3. **Monitorar logs:**
   - Configure alertas para erros críticos
   - Revise logs regularmente

4. **Firewall:**
   - Mantenha apenas portas necessárias abertas (80, 443, 22)
   - Use fail2ban para proteção contra brute force

5. **Senhas:**
   - Use senhas fortes
   - Troque senhas padrão
   - Use chaves SSH ao invés de senhas quando possível

## 📚 Documentação Adicional

- [Documentação do Django Deployment](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [Documentação do Gunicorn](https://gunicorn.org/)
- [Documentação do Nginx](https://nginx.org/en/docs/)
- [Documentação do PostgreSQL](https://www.postgresql.org/docs/)

## 🆘 Suporte

Em caso de problemas, verifique:
1. Logs do sistema (`journalctl -u gunicorn`)
2. Logs do Nginx (`/var/log/nginx/`)
3. Logs da aplicação (`/var/log/gunicorn/`)
4. Status dos serviços (`systemctl status`)

---

**Última atualização:** 2025-01-XX

