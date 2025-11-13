# Guia de Deploy - Railway

## Problemas comuns e soluções

### Arquivos estáticos retornando 404

O projeto está configurado para usar **WhiteNoise** para servir arquivos estáticos em produção.

#### Verificações necessárias:

1. **Execute collectstatic antes do deploy:**
   ```bash
   python manage.py collectstatic --noinput
   ```

2. **Verifique se o WhiteNoise está instalado:**
   ```bash
   pip install whitenoise
   ```

3. **Verifique a configuração no Railway:**
   - O comando de start deve incluir `collectstatic`:
     ```
     python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn saas_viabilidade.wsgi:application --bind 0.0.0.0:$PORT
     ```

4. **Variáveis de ambiente no Railway:**
   - `DEBUG=False` (importante para WhiteNoise funcionar corretamente)
   - `ALLOWED_HOSTS=verificador.up.railway.app,seu-dominio.com`
   - `CSRF_TRUSTED_ORIGINS=https://verificador.up.railway.app,https://seu-dominio.com`

## Configuração do Railway

### 1. Variáveis de Ambiente

Configure as seguintes variáveis no Railway:

```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=verificador.up.railway.app
CSRF_TRUSTED_ORIGINS=https://verificador.up.railway.app
DATABASE_URL=postgresql://...
```

### 2. Configuração Automática

O Railway detecta automaticamente projetos Python através do arquivo `requirements.txt` e usa o `Procfile` para iniciar a aplicação.

O `Procfile` contém:
```
web: bash start.sh
```

O script `start.sh`:
- Verifica se `DATABASE_URL` está configurada
- Executa as migrações do banco de dados
- Coleta arquivos estáticos
- Inicia o servidor Gunicorn

**Importante:** O Railway executa automaticamente o `Procfile`. Não é necessário configurar comandos manualmente.

### 3. Build Command (opcional)

Se quiser executar collectstatic durante o build:

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

## Troubleshooting

### Erro: "MIME type ('text/html') is not a supported stylesheet MIME type"

**Causa:** Os arquivos estáticos não estão sendo encontrados e o servidor está retornando uma página HTML (404) ao invés do arquivo CSS/JS.

**Solução:**
1. Verifique se `collectstatic` foi executado
2. Verifique se o diretório `staticfiles` existe e contém os arquivos
3. Verifique se o WhiteNoise está no middleware (deve estar logo após SecurityMiddleware)
4. Verifique se `DEBUG=False` em produção

### Erro: "404 (Not Found)" para arquivos estáticos

**Solução:**
1. Execute `python manage.py collectstatic --noinput` localmente e verifique se os arquivos são criados
2. No Railway, verifique os logs para ver se o collectstatic foi executado
3. Verifique se `STATIC_ROOT` está configurado corretamente

### Erro: "Content Security Policy violation"

**Solução:**
O CSP foi atualizado para permitir arquivos do próprio domínio dinamicamente. Se ainda houver problemas, verifique:
1. Se o domínio está correto nas variáveis de ambiente
2. Se o CSP está permitindo o domínio do Railway
3. O CSP agora inclui `blob:` e `data:` para fontes, o que deve resolver a maioria dos problemas

### Erro: "CSRF verification failed" (403)

**Causa:** O token CSRF não está sendo enviado corretamente ou o domínio não está em `CSRF_TRUSTED_ORIGINS`.

**Solução:**
1. Configure `CSRF_TRUSTED_ORIGINS` no Railway com o domínio completo (ex: `https://verificador.up.railway.app`)
2. Se não configurar, o sistema tentará adicionar automaticamente baseado em `ALLOWED_HOSTS`
3. Certifique-se de que `DEBUG=False` em produção
4. As configurações de CSRF foram ajustadas para usar `SameSite=Lax` e cookies ao invés de sessões para melhor compatibilidade

## Checklist de Deploy

- [ ] Todas as variáveis de ambiente configuradas
- [ ] `DEBUG=False` em produção
- [ ] `ALLOWED_HOSTS` inclui o domínio do Railway
- [ ] `CSRF_TRUSTED_ORIGINS` inclui o domínio do Railway
- [ ] `collectstatic` está sendo executado
- [ ] WhiteNoise está instalado e no middleware
- [ ] Gunicorn está instalado
- [ ] Banco de dados está configurado e acessível
- [ ] Migrações foram executadas

