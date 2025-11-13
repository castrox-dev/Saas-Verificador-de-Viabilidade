# Guia de Deploy no Railway

Este documento explica como fazer deploy do projeto no Railway.

## Pré-requisitos

1. Conta no [Railway](https://railway.app)
2. Projeto conectado ao GitHub (ou outro repositório)
3. Banco de dados Neon configurado (ou outro PostgreSQL)

## Configuração no Railway

### 1. Variáveis de Ambiente

Configure as seguintes variáveis de ambiente no Railway:

#### Obrigatórias:
- `DATABASE_URL`: String de conexão do PostgreSQL (Neon)
  - Exemplo: `postgresql://user:password@host/dbname?sslmode=require`
- `SECRET_KEY`: Chave secreta do Django (gere uma nova e segura)
  - Gere com: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

#### Opcionais (mas recomendadas):
- `ALLOWED_HOSTS`: Domínios permitidos (separados por vírgula)
  - Exemplo: `seu-dominio.railway.app,www.seu-dominio.com`
- `CSRF_TRUSTED_ORIGINS`: Origens confiáveis para CSRF (separadas por vírgula)
  - Exemplo: `https://seu-dominio.railway.app,https://www.seu-dominio.com`
- `DEBUG`: `False` (sempre False em produção)
- `RAILWAY_PUBLIC_DOMAIN`: Domínio público do Railway (geralmente configurado automaticamente)

### 2. Build e Deploy

O Railway detecta automaticamente:
- **Python** através do `requirements.txt`
- **Comando de start** através do `Procfile`

O `Procfile` está configurado para:
1. Executar migrações do banco de dados
2. Coletar arquivos estáticos
3. Iniciar o servidor Gunicorn na porta `$PORT` (fornecida pelo Railway)

### 3. Domínio Personalizado (Opcional)

Se você configurar um domínio personalizado no Railway:
1. Adicione o domínio em `ALLOWED_HOSTS`
2. Adicione `https://seu-dominio.com` em `CSRF_TRUSTED_ORIGINS`

## Estrutura de Arquivos

### Procfile
```
web: bash start.sh
```

### start.sh
O script `start.sh` executa:
1. Verificação de `DATABASE_URL`
2. Migrações (`python manage.py migrate`)
3. Coleta de arquivos estáticos (`python manage.py collectstatic`)
4. Inicialização do Gunicorn

## Detecção Automática do Railway

O `settings.py` detecta automaticamente se está rodando no Railway através das variáveis:
- `RAILWAY_ENVIRONMENT`
- `RAILWAY_PUBLIC_DOMAIN`

Quando detectado:
- `DEBUG` é automaticamente definido como `False`
- `ALLOWED_HOSTS` é configurado automaticamente
- `CSRF_TRUSTED_ORIGINS` é configurado automaticamente

## Troubleshooting

### Erro: "DATABASE_URL não está configurada"
- Verifique se a variável `DATABASE_URL` está configurada no Railway
- Certifique-se de que a string de conexão está correta

### Erro: "DisallowedHost"
- Adicione o domínio em `ALLOWED_HOSTS`
- Ou configure `RAILWAY_PUBLIC_DOMAIN` no Railway

### Erro: CSRF verification failed
- Adicione a origem em `CSRF_TRUSTED_ORIGINS`
- Certifique-se de usar `https://` (não `http://`)

### Arquivos estáticos não carregam
- O WhiteNoise está configurado para servir arquivos estáticos
- Certifique-se de que `collectstatic` está sendo executado (já está no `start.sh`)

## Comandos Úteis

### Ver logs no Railway
```bash
railway logs
```

### Executar comandos Django no Railway
```bash
railway run python manage.py <comando>
```

### Acessar shell do Django
```bash
railway run python manage.py shell
```

## Checklist de Deploy

- [ ] `DATABASE_URL` configurada no Railway
- [ ] `SECRET_KEY` configurada (nova e segura)
- [ ] `DEBUG=False` ou não configurado (será False automaticamente)
- [ ] `ALLOWED_HOSTS` configurado (ou deixar automático)
- [ ] `CSRF_TRUSTED_ORIGINS` configurado (ou deixar automático)
- [ ] Domínio personalizado configurado (se aplicável)
- [ ] Migrações executadas com sucesso
- [ ] Arquivos estáticos coletados
- [ ] Servidor iniciado corretamente

## Notas Importantes

1. **Banco de Dados**: O projeto está configurado para usar apenas PostgreSQL (Neon). Não há fallback para SQLite.

2. **Sessão Única**: A funcionalidade de sessão única está implementada mas comentada. Veja `docs/sessao-unica.md` para ativar.

3. **Arquivos de Mídia**: Arquivos enviados pelos usuários são salvos em `media/`. Considere usar um serviço de storage (S3, etc.) para produção.

4. **Logs**: Os logs são exibidos automaticamente no Railway. Configure `LOGGING` em `settings.py` se precisar de logs personalizados.

