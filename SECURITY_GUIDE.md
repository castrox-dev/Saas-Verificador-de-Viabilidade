# 🔒 Guia de Segurança - SaaS Verificador de Viabilidade

## **VULNERABILIDADES CORRIGIDAS**

### ✅ **1. ISOLAMENTO DE DADOS**
- **Problema:** Middleware permitia acesso sem autenticação
- **Solução:** `SecureCompanyMiddleware` com validação obrigatória
- **Arquivo:** `core/middleware_security.py`

### ✅ **2. VALIDAÇÃO DE ARQUIVOS**
- **Problema:** Validação baseada apenas em extensão
- **Solução:** `SecureFileValidator` com verificação de conteúdo real
- **Formatos suportados:** .xlsx, .xls, .csv, .kml, .kmz
- **Arquivo:** `core/security_validators.py`

### ✅ **3. RATE LIMITING**
- **Problema:** Sem proteção contra ataques de força bruta
- **Solução:** Sistema de rate limiting por IP e usuário
- **Arquivo:** `core/rate_limiting.py`

### ✅ **4. HEADERS DE SEGURANÇA**
- **Problema:** Falta de headers de segurança
- **Solução:** `SecurityHeadersMiddleware` com CSP e outros headers
- **Arquivo:** `core/security_headers.py`

### ✅ **5. VALIDAÇÃO DE SENHAS**
- **Problema:** Senhas fracas permitidas
- **Solução:** `ComplexPasswordValidator` com regras rigorosas
- **Arquivo:** `core/validators.py`

## **CONFIGURAÇÕES DE PRODUÇÃO**

### **Variáveis de Ambiente Críticas**
```bash
# OBRIGATÓRIO: Altere antes do deploy
SECRET_KEY=sua-chave-super-secreta-aqui
DEBUG=False

# Banco de dados
DB_NAME=saas_viabilidade
DB_USER=usuario_db
DB_PASSWORD=senha_forte_db
DB_HOST=localhost
DB_PORT=5432

# Cache Redis
REDIS_URL=redis://localhost:6379/1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-app
```

### **Configurações de Segurança Implementadas**

#### **1. Middleware de Segurança**
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware_security.SecureCompanyMiddleware',  # ✅ SEGURO
    'core.security_headers.SecurityHeadersMiddleware',  # ✅ SEGURO
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

#### **2. Configurações de Sessão**
```python
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
```

#### **3. Headers de Segurança**
- Content Security Policy (CSP)
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security
- Referrer-Policy: strict-origin-when-cross-origin

## **DEPLOY SEGURO**

### **1. Preparação**
```bash
# 1. Copiar arquivo de ambiente
cp env.example .env

# 2. Editar variáveis críticas
nano .env

# 3. Instalar dependências
pip install -r requirements_production.txt

# 4. Executar deploy
chmod +x deploy.sh
./deploy.sh
```

### **2. Configuração do Servidor**

#### **Nginx (Recomendado)**
```nginx
server {
    listen 443 ssl http2;
    server_name rmsys.com.br www.rmsys.com.br;
    
    # SSL obrigatório
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    
    # Headers de segurança
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Proxy para Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### **PostgreSQL**
```sql
-- Criar banco de dados
CREATE DATABASE saas_viabilidade;
CREATE USER saas_user WITH PASSWORD 'senha_forte';
GRANT ALL PRIVILEGES ON DATABASE saas_viabilidade TO saas_user;
```

#### **Redis**
```bash
# Instalar Redis
sudo apt install redis-server

# Configurar Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### **3. Monitoramento e Backup**

#### **Backup Automático**
```bash
# Configurar cron
crontab crontab_example.txt

# Executar backup manual
python backup_script.py
```

#### **Logs de Segurança**
```bash
# Verificar logs de segurança
tail -f logs/security.log

# Verificar logs gerais
tail -f logs/django.log
```

## **TESTES DE SEGURANÇA**

### **1. Teste de Isolamento de Dados**
```bash
# Teste 1: Acesso sem autenticação
curl -I https://rmsys.com.br/empresa-teste/

# Deve retornar: 403 Forbidden
```

### **2. Teste de Rate Limiting**
```bash
# Teste 2: Múltiplas tentativas de login
for i in {1..10}; do
  curl -X POST https://rmsys.com.br/rm/login/ \
    -d "username=admin&password=wrong"
done

# Deve bloquear após 5 tentativas
```

### **3. Teste de Upload de Arquivos**
```bash
# Teste 3: Upload de arquivo malicioso
curl -X POST https://rmsys.com.br/empresa/upload/ \
  -F "file=@malicious.exe" \
  -F "description=test"

# Deve rejeitar arquivo .exe
```

## **MANUTENÇÃO DE SEGURANÇA**

### **Rotinas Diárias**
1. ✅ Verificar logs de segurança
2. ✅ Monitorar tentativas de acesso
3. ✅ Verificar espaço em disco
4. ✅ Validar backups

### **Rotinas Semanais**
1. ✅ Atualizar dependências
2. ✅ Revisar logs de acesso
3. ✅ Testar restauração de backup
4. ✅ Verificar certificados SSL

### **Rotinas Mensais**
1. ✅ Auditoria de usuários
2. ✅ Revisão de permissões
3. ✅ Teste de penetração
4. ✅ Atualização de senhas

## **ALERTAS DE SEGURANÇA**

### **Sinais de Ataque**
- Múltiplas tentativas de login falhadas
- Upload de arquivos suspeitos
- Acesso a URLs não autorizadas
- Padrões anômalos de tráfego

### **Ações Imediatas**
1. 🔴 Bloquear IP suspeito
2. 🔴 Alterar senhas administrativas
3. 🔴 Verificar logs detalhados
4. 🔴 Notificar administradores

## **CONTATOS DE EMERGÊNCIA**

- **Admin Principal:** admin@rmsys.com.br
- **Suporte Técnico:** suporte@rmsys.com.br
- **Emergência:** +55 11 99999-9999

---

## **✅ CHECKLIST DE SEGURANÇA**

- [ ] SECRET_KEY alterada
- [ ] DEBUG=False em produção
- [ ] SSL/TLS configurado
- [ ] Banco PostgreSQL configurado
- [ ] Redis configurado
- [ ] Backup automático ativo
- [ ] Logs de segurança funcionando
- [ ] Rate limiting ativo
- [ ] Headers de segurança aplicados
- [ ] Validação de arquivos funcionando
- [ ] Isolamento de dados testado
- [ ] Senhas administrativas alteradas
- [ ] Monitoramento configurado
- [ ] Testes de segurança executados

**🎯 SISTEMA SEGURO PARA PRODUÇÃO!**
