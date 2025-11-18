# 🔧 Configuração de Variáveis de Ambiente na VPS

Como o arquivo `.env` não é commitado no Git (por segurança), você precisa configurá-lo manualmente na VPS após clonar o repositório.

## 📋 Opções para Configurar Variáveis de Ambiente

### Opção 1: Usar Arquivo .env (Recomendado)

Esta é a forma mais simples e já está configurada no sistema.

#### Passo 1: Criar arquivo .env

```bash
cd /var/www/saas-viabilidade

# Usar script automatizado
bash setup-env.sh

# OU criar manualmente
cp .env.example.vps .env
nano .env
```

#### Passo 2: Configurar variáveis

Edite o arquivo `.env` com suas configurações:

```bash
nano .env
```

Exemplo mínimo necessário:

```env
SECRET_KEY=django-insecure-sua-chave-secreta-muito-forte-aqui
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
CSRF_TRUSTED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_banco
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
DEFAULT_FROM_EMAIL=seu-email@gmail.com
```

#### Passo 3: Configurar permissões

```bash
chmod 600 .env
chown appuser:appuser .env
```

#### Passo 4: Reiniciar serviços

```bash
sudo systemctl restart gunicorn
```

**Vantagens:**
- ✅ Fácil de gerenciar
- ✅ Já está configurado no `gunicorn.service`
- ✅ Fácil de fazer backup
- ✅ Permite múltiplos ambientes (.env.prod, .env.staging)

---

### Opção 2: Variáveis de Ambiente do Sistema

Você pode definir variáveis de ambiente diretamente no sistema Linux.

#### Configurar em /etc/environment (todas as sessões)

```bash
sudo nano /etc/environment
```

Adicionar:

```bash
SECRET_KEY="sua-chave-secreta"
DEBUG="False"
ALLOWED_HOSTS="seu-dominio.com,www.seu-dominio.com"
DATABASE_URL="postgresql://usuario:senha@localhost:5432/nome_banco"
```

#### Configurar no perfil do usuário (apenas sessão do usuário)

```bash
sudo -u appuser nano ~/.bashrc
# ou
sudo -u appuser nano ~/.profile
```

Adicionar:

```bash
export SECRET_KEY="sua-chave-secreta"
export DEBUG="False"
export ALLOWED_HOSTS="seu-dominio.com,www.seu-dominio.com"
export DATABASE_URL="postgresql://usuario:senha@localhost:5432/nome_banco"
```

**Desvantagens:**
- ❌ Mais difícil de gerenciar
- ❌ Precisa atualizar systemd service para não usar EnvironmentFile

---

### Opção 3: Variáveis no Systemd Service (Apenas para Gunicorn)

Você pode definir variáveis diretamente no arquivo `gunicorn.service`:

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

```ini
[Service]
Environment="SECRET_KEY=sua-chave-secreta"
Environment="DEBUG=False"
Environment="ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com"
Environment="DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_banco"
# Remover ou comentar a linha EnvironmentFile se usar esta opção
# EnvironmentFile=/var/www/saas-viabilidade/.env
```

Depois:

```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

**Desvantagens:**
- ❌ Configuração misturada com código do serviço
- ❌ Não funciona para comandos Django executados manualmente
- ❌ Difícil de fazer backup

---

## 🚀 Processo Recomendado (Opção 1)

### 1. Após clonar repositório

```bash
cd /var/www/saas-viabilidade
bash setup-env.sh
```

Este script irá:
- Criar `.env` a partir de `.env.example.vps`
- Gerar SECRET_KEY automaticamente
- Configurar permissões corretas

### 2. Editar configurações

```bash
nano .env
```

### 3. Verificar configurações

```bash
# Testar se o Django consegue carregar as variáveis
cd /var/www/saas-viabilidade
source venv/bin/activate
python manage.py check --deploy
```

### 4. Reiniciar serviços

```bash
sudo systemctl restart gunicorn
```

---

## 🔒 Segurança do Arquivo .env

O arquivo `.env` contém informações sensíveis. Siga estas práticas:

### Permissões Corretas

```bash
# Apenas o dono pode ler/escrever
chmod 600 .env

# Garantir que o dono é o usuário da aplicação
chown appuser:appuser .env
```

### Backup Seguro

```bash
# Fazer backup (sem incluir em repositórios Git!)
cp .env .env.backup.$(date +%Y%m%d)
```

### Não Commitar

Sempre verifique que `.env` está no `.gitignore`:

```bash
cat .gitignore | grep .env
# Deve mostrar: .env
```

---

## 🔄 Atualizar Variáveis Após Deploy

### Quando você fizer `git pull`:

```bash
cd /var/www/saas-viabilidade
git pull

# O .env não será sobrescrito, mas você pode precisar adicionar novas variáveis
# Verifique se há novas variáveis no .env.example.vps:
diff .env .env.example.vps
```

Se houver novas variáveis:

```bash
# Adicionar manualmente ao .env
nano .env

# OU usar script para mesclar (cuidado para não sobrescrever valores existentes)
```

---

## 📝 Exemplo de Arquivo .env Completo

```env
# Segurança
SECRET_KEY=django-insecure-xyz123...sua-chave-forte-aqui
DEBUG=False
IS_LOCAL_DEV=False

# Domínios
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com,127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com

# Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/saas_viabilidade
DB_CONN_MAX_AGE=600

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app-aqui
DEFAULT_FROM_EMAIL=seu-email@gmail.com
SERVER_EMAIL=seu-email@gmail.com

# APIs Opcionais
OPENROUTESERVICE_API_KEY=

# Configurações do Sistema
ROUTING_TIMEOUT=15
VIABILIDADE_VIABLE=300
VIABILIDADE_LIMITADA=800
VIABILIDADE_INVIAVEL=800
```

---

## ✅ Checklist de Configuração

- [ ] Arquivo `.env` criado na VPS
- [ ] SECRET_KEY configurada (gerada automaticamente pelo script)
- [ ] ALLOWED_HOSTS configurado com domínio correto
- [ ] CSRF_TRUSTED_ORIGINS configurado com HTTPS
- [ ] DATABASE_URL configurada corretamente
- [ ] Configurações de email configuradas
- [ ] Permissões do arquivo configuradas (600)
- [ ] Dono do arquivo configurado (appuser)
- [ ] Gunicorn reiniciado após configuração
- [ ] Django consegue carregar variáveis (`python manage.py check`)

---

## 🆘 Troubleshooting

### Erro: "DATABASE_URL não está configurada"

**Causa:** Variáveis não estão sendo carregadas.

**Solução:**
```bash
# Verificar se .env existe e tem permissões corretas
ls -la /var/www/saas-viabilidade/.env

# Verificar se o gunicorn.service está usando EnvironmentFile
sudo systemctl cat gunicorn.service | grep EnvironmentFile

# Recarregar variáveis manualmente e testar
cd /var/www/saas-viabilidade
source .env
python manage.py check
```

### Erro: "SECRET_KEY deve ser alterado em produção"

**Causa:** SECRET_KEY está com valor padrão.

**Solução:**
```bash
# Gerar nova SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Adicionar ao .env
nano .env
# Editar linha: SECRET_KEY=nova-chave-gerada
```

### Variáveis não estão sendo carregadas após restart

**Solução:**
```bash
# Verificar se o serviço está usando o EnvironmentFile correto
sudo systemctl show gunicorn.service | grep EnvironmentFile

# Recarregar daemon do systemd
sudo systemctl daemon-reload

# Reiniciar serviço
sudo systemctl restart gunicorn

# Verificar logs
sudo journalctl -u gunicorn -f
```

---

**Última atualização:** 2025-01-XX

