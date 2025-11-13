# Verificação de Rotas para Deploy

Este documento verifica todas as rotas e configurações de autenticação para garantir que estão corretas para o deploy no Railway.

## Configurações de Login (settings.py)

```python
LOGIN_REDIRECT_URL = "/dashboard/"  # Usa dashboard_redirect que redireciona corretamente
LOGOUT_REDIRECT_URL = "/rm/login/"
LOGIN_URL = "/rm/login/"
```

## Estrutura de Rotas

### Rotas Principais (saas_viabilidade/urls.py)
- `/` → Redireciona para `/rm/login/`
- `/dashboard/` → `dashboard_redirect` (redireciona conforme papel do usuário)
- `/rm/` → Inclui todas as rotas RM
- `/<company_slug>/` → Inclui todas as rotas da empresa
- `/verificador/` → Verificador global

### Rotas RM (core/urls_rm.py)
- `/rm/login/` → `rm_login_view` (login para admins RM)
- `/rm/logout/` → `logout_view`
- `/rm/admin/` → `rm_admin_dashboard` (requer @rm_admin_required)
- `/rm/empresas/` → `company_list` (requer @rm_admin_required)
- `/rm/usuarios/` → `rm_user_list` (requer @rm_admin_required)
- `/rm/mapas/` → `rm_map_list` (requer @rm_admin_required)
- `/rm/relatorios/` → `rm_reports` (requer @rm_admin_required)

### Rotas de Empresa (core/urls_company.py)
- `/<company_slug>/login/` → `company_login_view` (login para usuários da empresa)
- `/<company_slug>/logout/` → `company_logout_view`
- `/<company_slug>/painel/` → `company_dashboard` (requer @company_access_required)
- `/<company_slug>/verificador/` → `company_verificador` (requer @company_access_required)
- `/<company_slug>/upload/` → `company_map_upload_page` (requer @company_access_required)

## Fluxo de Login

### Login RM (rm_login_view)
1. POST em `/rm/login/` com username/email e password
2. Autentica o usuário
3. Verifica se é admin RM ou superuser
4. Se sim, faz login e redireciona para `rm:admin_dashboard` → `/rm/admin/`
5. Se não, mostra erro "Credenciais inválidas"

### Login Empresa (company_login_view)
1. POST em `/<company_slug>/login/` com username/email e password
2. Autentica o usuário
3. Verifica se o usuário pertence à empresa do slug
4. Se sim, faz login e redireciona conforme o papel:
   - COMPANY_ADMIN → `company:dashboard` → `/<company_slug>/painel/`
   - COMPANY_USER → `/<company_slug>/verificador/`
5. Se não, mostra erro "Credenciais inválidas para esta empresa"

### Dashboard Redirect (dashboard_redirect)
Redireciona conforme o papel do usuário:
- RM Admin ou Superuser → `/rm/admin/`
- COMPANY_ADMIN → `/<company_slug>/painel/`
- COMPANY_USER → `/<company_slug>/verificador/`
- Fallback → `/rm/admin/`

## Decorators de Permissão

### @rm_admin_required
- Verifica se o usuário é admin RM ou superuser
- Se não, redireciona para `/rm/login/`
- Usado em: `rm_admin_dashboard`, `company_list`, `rm_user_list`, etc.

### @company_access_required
- Verifica se o usuário pertence à empresa do slug
- RM admins e superusers sempre têm acesso
- Se `require_admin=True`, também verifica se é COMPANY_ADMIN
- Se `allow_user_role=False`, COMPANY_USER não pode acessar (exceto verificador)
- Usado em: `company_dashboard`, `company_verificador`, etc.

## Middleware SecureCompanyMiddleware

O middleware `SecureCompanyMiddleware`:
1. Detecta o slug da empresa na URL (primeiro segmento)
2. Se for `/rm/`, marca como acesso RM
3. Se for slug de empresa:
   - Login: permite acesso sem autenticação
   - Outras rotas: exige autenticação e verifica se o usuário pertence à empresa
   - RM admins e superusers sempre têm acesso
   - Se não autorizado, retorna 403 e faz logout

## Possíveis Problemas e Soluções

### Problema: Erro 403 após login
**Causa possível:** Usuário não tem permissões corretas ou não está sendo reconhecido como admin RM
**Solução:** Verificar se o usuário tem `role='RM'` ou `is_superuser=True`

### Problema: Redirecionamento incorreto
**Causa possível:** LOGIN_REDIRECT_URL não está sendo usado corretamente
**Solução:** A view `rm_login_view` redireciona diretamente para `rm:admin_dashboard`, ignorando LOGIN_REDIRECT_URL

### Problema: Loop de redirecionamento
**Causa possível:** Decorator redirecionando para login mesmo estando autenticado
**Solução:** Verificar se o decorator está verificando corretamente as permissões

## Checklist de Verificação

- [ ] Usuário tem `role='RM'` ou `is_superuser=True` para acessar `/rm/admin/`
- [ ] Usuário tem `company` associada para acessar rotas de empresa
- [ ] Middleware está permitindo acesso correto conforme o papel do usuário
- [ ] Decorators estão verificando permissões corretamente
- [ ] Redirecionamentos estão funcionando após login
- [ ] LOGIN_URL está configurado corretamente (`/rm/login/`)
- [ ] LOGIN_REDIRECT_URL está configurado corretamente (`/dashboard/`)
- [ ] LOGOUT_REDIRECT_URL está configurado corretamente (`/rm/login/`)

## Comandos Úteis para Debug

```bash
# Verificar usuário no Django shell
python manage.py shell
>>> from core.models import CustomUser
>>> user = CustomUser.objects.get(username='seu_usuario')
>>> print(f"Role: {user.role}")
>>> print(f"is_rm_admin: {user.is_rm_admin}")
>>> print(f"is_superuser: {user.is_superuser}")
>>> print(f"Company: {user.company}")
```

