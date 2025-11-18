# 🚀 Migração para VPS Hostinger

Este guia fornece instruções rápidas para migrar o sistema do Railway para uma VPS da Hostinger.

## 📦 Arquivos Criados

Os seguintes arquivos foram criados para facilitar a migração:

- `setup_vps.sh` - Script de setup inicial da VPS
- `deploy_vps.sh` - Script de deploy da aplicação
- `gunicorn_config.py` - Configuração do Gunicorn
- `gunicorn.service` - Arquivo systemd para Gunicorn
- `nginx.conf` - Configuração do Nginx
- `.env.example.vps` - Exemplo de arquivo .env para VPS
- `docs/vps-migration.md` - Documentação completa de migração

## 🚀 Início Rápido

### 1. Preparar VPS

```bash
# Conectar na VPS
ssh root@seu-ip-vps

# Fazer upload do setup_vps.sh
# (ou clonar o repositório)

# Executar setup
chmod +x setup_vps.sh
sudo ./setup_vps.sh
```

### 2. Configurar Aplicação

```bash
# Clonar repositório
cd /var/www
git clone <seu-repositorio> saas-viabilidade
cd saas-viabilidade

# Configurar .env (o arquivo .env não vai para o Git por segurança)
bash setup-env.sh  # Script automatizado que cria .env e gera SECRET_KEY
nano .env  # Editar com suas configurações
```

**Importante:** O arquivo `.env` não é commitado no Git. Use o script `setup-env.sh` para criá-lo na VPS após clonar o repositório. Veja `docs/vps-env-setup.md` para mais opções.

### 3. Configurar Serviços

```bash
# Instalar serviço Gunicorn
sudo cp gunicorn.service /etc/systemd/system/
sudo nano /etc/systemd/system/gunicorn.service  # Ajustar usuário/caminhos
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn

# Configurar Nginx
sudo cp nginx.conf /etc/nginx/sites-available/saas-viabilidade
sudo nano /etc/nginx/sites-available/saas-viabilidade  # Ajustar domínio
sudo ln -s /etc/nginx/sites-available/saas-viabilidade /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Configurar SSL

```bash
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

### 5. Deploy

```bash
chmod +x deploy_vps.sh
./deploy_vps.sh
```

## 📋 Checklist

- [ ] VPS configurada e atualizada
- [ ] PostgreSQL instalado e banco de dados criado
- [ ] Backup do banco de dados do Railway realizado
- [ ] Backup restaurado na VPS
- [ ] Aplicação clonada e .env configurado
- [ ] Gunicorn configurado e rodando
- [ ] Nginx configurado e rodando
- [ ] SSL configurado (Let's Encrypt)
- [ ] Testes realizados
- [ ] Backups automáticos configurados

## 📚 Documentação Completa

Para instruções detalhadas, consulte: `docs/vps-migration.md`

## 🔧 Comandos Úteis

```bash
# Ver status dos serviços
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql

# Ver logs
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/saas-viabilidade-error.log

# Reiniciar serviços
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Fazer deploy de atualizações
cd /var/www/saas-viabilidade
git pull
./deploy_vps.sh
```

## 🆘 Problemas Comuns

Veja a seção de troubleshooting em `docs/vps-migration.md`

