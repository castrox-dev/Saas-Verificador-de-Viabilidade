# 🚀 Guia de Atualização do Projeto na VPS

Este guia mostra como atualizar o projeto na VPS Hostinger após fazer mudanças no código local.

## 📋 Pré-requisitos

- Acesso SSH à VPS
- Git configurado e repositório atualizado localmente
- Mudanças já commitadas e enviadas para o repositório remoto

## 🔄 Processo de Atualização

### 1. Conectar na VPS via SSH

```bash
ssh seu-usuario@seu-ip-ou-dominio
```

### 2. Navegar para o Diretório do Projeto

```bash
cd /usr/local/lsws/Example/html/demo
```

### 3. Ativar o Ambiente Virtual

```bash
source venv/bin/activate
```

Você verá `(venv)` no início da linha do terminal quando estiver ativado.

### 4. Fazer Pull das Atualizações

```bash
git pull origin main
```

**Nota:** Se sua branch principal for `master`, use:
```bash
git pull origin master
```

### 5. Instalar/Atualizar Dependências

```bash
pip install -r requirements.txt
```

Isso atualiza todas as dependências, incluindo correções como a versão do `psycopg-binary`.

### 6. Executar Migrações do Banco de Dados

```bash
python manage.py migrate
```

**Importante:** Se houver conflitos de migração, execute primeiro:
```bash
python manage.py makemigrations --merge
python manage.py migrate
```

### 7. Coletar Arquivos Estáticos

```bash
python manage.py collectstatic --noinput --clear
```

Isso coleta todos os arquivos estáticos (CSS, JS, imagens), incluindo novos arquivos como `global-loading.js`.

### 8. Sair do Ambiente Virtual

```bash
deactivate
```

### 9. Reiniciar o Serviço Gunicorn

```bash
sudo systemctl restart gunicorn
```

### 10. Verificar Status do Gunicorn

```bash
sudo systemctl status gunicorn
```

Verifique se o status está `active (running)` e sem erros.

## 📝 Comandos Completos em Sequência

Execute todos os comandos de uma vez:

```bash
cd /usr/local/lsws/Example/html/demo
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput --clear
deactivate
sudo systemctl restart gunicorn
sudo systemctl status gunicorn
```

## 🔍 Verificação e Troubleshooting

### Verificar Logs do Gunicorn

Se houver problemas, verifique os logs:

```bash
# Últimas 50 linhas de log
sudo journalctl -u gunicorn -n 50 --no-pager

# Logs em tempo real
sudo journalctl -u gunicorn -f
```

### Verificar Logs do Nginx

```bash
sudo tail -f /var/log/nginx/error.log
```

### Verificar se o Servidor Está Respondendo

```bash
curl http://127.0.0.1:8000
```

### Verificar Processos Python

```bash
ps aux | grep gunicorn
```

## ⚠️ Problemas Comuns

### Erro: "git pull" falha com "dubious ownership"

**Solução:**
```bash
git config --global --add safe.directory /usr/local/lsws/Example/html/demo
```

### Erro: "Conflicting migrations detected"

**Solução:**
```bash
python manage.py makemigrations --merge
python manage.py migrate
```

### Erro: "ModuleNotFoundError" após atualizar dependências

**Solução:**
```bash
# Reinstalar todas as dependências
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Erro: Gunicorn não inicia

**Solução:**
```bash
# Verificar configuração do serviço
sudo systemctl status gunicorn
sudo journalctl -u gunicorn -n 100

# Verificar se o arquivo gunicorn.service está correto
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

### Arquivos Estáticos Não Atualizados

**Solução:**
```bash
# Limpar cache e recolher estáticos
python manage.py collectstatic --noinput --clear

# Verificar permissões
sudo chown -R www-data:www-data /usr/local/lsws/Example/html/demo/staticfiles
```

## 📦 O Que É Atualizado

Quando você executa este processo, as seguintes coisas são atualizadas:

- ✅ Código Python (views, models, utils, etc.)
- ✅ Templates HTML
- ✅ Arquivos JavaScript e CSS
- ✅ Dependências Python (requirements.txt)
- ✅ Migrações do banco de dados
- ✅ Arquivos estáticos coletados
- ✅ Configurações do Django

## 🔄 Fluxo Completo de Deploy

1. **Local:** Fazer mudanças no código
2. **Local:** Testar localmente
3. **Local:** Commit e push para o repositório
   ```bash
   git add .
   git commit -m "Descrição das mudanças"
   git push origin main
   ```
4. **VPS:** Conectar via SSH
5. **VPS:** Executar os comandos de atualização (acima)
6. **VPS:** Verificar se tudo está funcionando

## 📌 Dicas Importantes

- ⚠️ **Sempre faça backup antes de atualizar em produção**
- ✅ **Teste localmente antes de fazer deploy**
- ✅ **Verifique os logs após cada atualização**
- ✅ **Mantenha o ambiente virtual ativado durante as operações**
- ✅ **Use `--noinput` nos comandos para evitar interações**

## 🆘 Suporte

Se encontrar problemas:

1. Verifique os logs do Gunicorn
2. Verifique os logs do Nginx
3. Verifique se todas as dependências estão instaladas
4. Verifique se as migrações foram aplicadas
5. Verifique se os arquivos estáticos foram coletados

---

**Última atualização:** 2025-01-20

