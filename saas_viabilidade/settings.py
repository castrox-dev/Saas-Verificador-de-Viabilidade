from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

# Detectar ambiente de execução
IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") is not None or os.getenv("RAILWAY_PUBLIC_DOMAIN") is not None
IS_VPS = os.path.exists("/etc/nginx") or os.getenv("VPS_ENVIRONMENT") is not None
IS_PRODUCTION = not os.getenv("DEBUG", "").lower() in ("1", "true", "on", "yes") or IS_RAILWAY or IS_VPS

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

# DEBUG: Garantir que está desabilitado em produção
DEBUG_ENV = os.getenv("DEBUG", "True").lower() in ("1", "true", "on", "yes")
DEBUG = DEBUG_ENV and not IS_PRODUCTION

# Validação de segurança: Bloquear DEBUG=True em produção se não for desenvolvimento local explícito
IS_LOCAL_DEV = os.getenv("IS_LOCAL_DEV", "False").lower() in ("1", "true", "on", "yes")
if DEBUG and (IS_RAILWAY or IS_VPS) and not IS_LOCAL_DEV:
    raise ValueError("DEBUG não pode estar ativo em produção! Configure DEBUG=False ou IS_LOCAL_DEV=False.")

# Validar SECRET_KEY em produção
if not DEBUG and SECRET_KEY == "dev-secret-key-change-me":
    raise ValueError("SECRET_KEY deve ser alterado em produção! Use uma chave forte e única.")
ALLOWED_HOSTS_ENV = os.getenv("ALLOWED_HOSTS", "")

# Configurar ALLOWED_HOSTS automaticamente para Railway
if IS_RAILWAY:
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
    if railway_domain:
        # Django não suporta wildcards, então usamos apenas o domínio exato
        ALLOWED_HOSTS = [railway_domain]
    else:
        # Se não houver domínio específico, usar variável de ambiente ou fallback
        # O Railway geralmente fornece o domínio via RAILWAY_PUBLIC_DOMAIN
        # Se não estiver disponível, o usuário deve configurar ALLOWED_HOSTS manualmente
        ALLOWED_HOSTS = []
    
    # Adicionar hosts customizados se configurados
    if ALLOWED_HOSTS_ENV:
        ALLOWED_HOSTS.extend([h.strip() for h in ALLOWED_HOSTS_ENV.split(",") if h.strip()])
    
    # Se ainda estiver vazio, exigir configuração explícita
    if not ALLOWED_HOSTS:
        raise ValueError(
            "ALLOWED_HOSTS deve ser configurado! Defina a variável de ambiente ALLOWED_HOSTS "
            "com os domínios permitidos separados por vírgula (ex: 'rmsys.app,www.rmsys.app')."
        )
else:
    # Desenvolvimento local: permitir hosts locais apenas
    if ALLOWED_HOSTS_ENV:
        ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_ENV.split(",") if h.strip()]
    else:
        # Fallback seguro para desenvolvimento local apenas
        ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
    
    # Validar que não há wildcards
    if "*" in ALLOWED_HOSTS:
        raise ValueError(
            "Wildcard '*' não é permitido em ALLOWED_HOSTS por segurança. "
            "Configure domínios específicos ou use '127.0.0.1,localhost' para desenvolvimento."
        )

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "core",
    "ftth_viewer",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Deve vir logo após SecurityMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware_security.SecureCompanyMiddleware",
    "core.security_headers.SecurityHeadersMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "saas_viabilidade.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "saas_viabilidade.wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")
DB_CONN_MAX_AGE = int(os.getenv("DB_CONN_MAX_AGE", "0"))

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não está configurada. Defina a string de conexão (ex.: Neon) no arquivo .env."
    )

# Detectar se precisa de SSL (não precisa para localhost/local)
requires_ssl = (
    not DATABASE_URL.startswith("postgresql://localhost") 
    and not DATABASE_URL.startswith("postgres://localhost")
    and not DATABASE_URL.startswith("postgresql://127.0.0.1")
    and not DATABASE_URL.startswith("postgres://127.0.0.1")
)

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=DB_CONN_MAX_AGE,
        ssl_require=requires_ssl,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Configurações adicionais para arquivos estáticos
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Configuração do WhiteNoise para servir arquivos estáticos
# WhiteNoise permite que o Django sirva arquivos estáticos diretamente
# Usar WhiteNoise sempre, mas com configurações diferentes para dev/prod
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000 if not DEBUG else 0  # Cache de 1 ano em produção, sem cache em dev
WHITENOISE_USE_FINDERS = DEBUG  # Em dev, usar finders para arquivos não coletados
WHITENOISE_AUTOREFRESH = DEBUG  # Em dev, recarregar automaticamente
MEDIA_URL = "/media/"

# Configurar MEDIA_ROOT
# No Railway, volumes são montados em /data ou caminho configurado
# Em VPS, usar diretório padrão /var/www/saas-viabilidade/media
RAILWAY_VOLUME_PATH = os.getenv("RAILWAY_VOLUME_PATH", "/data")
VPS_MEDIA_ROOT = os.getenv("VPS_MEDIA_ROOT", "/var/www/saas-viabilidade/media")

if IS_RAILWAY and os.path.exists(RAILWAY_VOLUME_PATH):
    # Usar volume persistente do Railway
    MEDIA_ROOT = Path(RAILWAY_VOLUME_PATH) / "media"
    # Criar diretório se não existir
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    if DEBUG:
        print("=" * 80)
        print("✅ RAILWAY VOLUME CONFIGURADO CORRETAMENTE")
        print(f"✅ Arquivos de mídia sendo salvos em: {MEDIA_ROOT}")
        print("✅ Os arquivos persistem após reinicializações do container")
        print("=" * 80)
elif IS_VPS and os.path.exists(VPS_MEDIA_ROOT):
    # Usar diretório configurado para VPS
    MEDIA_ROOT = Path(VPS_MEDIA_ROOT)
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    if DEBUG:
        print("=" * 80)
        print("✅ VPS MEDIA ROOT CONFIGURADO CORRETAMENTE")
        print(f"✅ Arquivos de mídia sendo salvos em: {MEDIA_ROOT}")
        print("=" * 80)
else:
    # Usar diretório local (desenvolvimento ou sem volume configurado)
    MEDIA_ROOT = BASE_DIR / "media"
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    if IS_RAILWAY and not os.path.exists(RAILWAY_VOLUME_PATH):
        print("=" * 80)
        print("🚨 ATENÇÃO CRÍTICA: RAILWAY VOLUME NÃO CONFIGURADO!")
        print("=" * 80)
        print(f"❌ Railway Volume não encontrado em: {RAILWAY_VOLUME_PATH}")
        print(f"⚠️ Arquivos de mídia serão salvos em: {MEDIA_ROOT} (EFÊMERO)")
        print("")
        print("🔴 CONSEQUÊNCIA: Todos os arquivos de mapas serão PERDIDOS quando o")
        print("   container reiniciar. Você precisará re-enviar os arquivos a cada restart!")
        print("")
        print("✅ SOLUÇÃO: Configure um Railway Volume:")
        print("   1. Acesse seu projeto no Railway")
        print("   2. Vá em 'Volumes' → 'New Volume'")
        print(f"   3. Configure Mount Path: {RAILWAY_VOLUME_PATH}")
        print("   4. Escolha um tamanho adequado (ex: 10GB)")
        print("   5. Conecte o volume ao serviço Django")
        print("   6. Faça o deploy novamente")
        print("")
        print("📖 Documentação completa: docs/railway-volume-setup.md")
        print("=" * 80)

LOGIN_REDIRECT_URL = "/dashboard/"  # Usa dashboard_redirect que redireciona corretamente conforme papel do usuário
LOGOUT_REDIRECT_URL = "/rm/login/"
LOGIN_URL = "/rm/login/"

# Custom User Model
AUTH_USER_MODEL = 'core.CustomUser'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configurações de email
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('1', 'true', 'on', 'yes')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'castrox.dev@gmail.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Site ID para emails (necessário para password reset)
SITE_ID = 1

# CSRF and cookie security
CSRF_TRUSTED_ORIGINS_ENV = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in CSRF_TRUSTED_ORIGINS_ENV.split(",") if o.strip()]

# Adicionar hosts permitidos automaticamente (mesmo se já houver CSRF_TRUSTED_ORIGINS configurados)
# Se estiver no Railway, adicionar domínio automaticamente
if IS_RAILWAY:
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
    if railway_domain:
        origin = f"https://{railway_domain}"
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)
        # Também adicionar http:// para desenvolvimento/testes
        origin_http = f"http://{railway_domain}"
        if origin_http not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin_http)

# Adicionar https:// para cada host permitido (exceto wildcard)
for host in ALLOWED_HOSTS:
    if host and host != '*' and not host.startswith('*.'):
        # Adicionar com e sem www
        origin = f"https://{host}"
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)
        origin_http = f"http://{host}"
        if origin_http not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin_http)
        if not host.startswith('www.'):
            origin_www = f"https://www.{host}"
            if origin_www not in CSRF_TRUSTED_ORIGINS:
                CSRF_TRUSTED_ORIGINS.append(origin_www)

# Se ainda estiver vazio, adicionar padrões de desenvolvimento
if not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = [
        "https://127.0.0.1:8000",
        "https://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]

# Log para debug (apenas print, logger será configurado depois)
print(f"CSRF_TRUSTED_ORIGINS configurados: {CSRF_TRUSTED_ORIGINS}")
print(f"ALLOWED_HOSTS configurados: {ALLOWED_HOSTS}")

# Configurações de sessão - Segurança aprimorada
SESSION_COOKIE_AGE = 3600  # 1 hora
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax' if DEBUG else 'Lax'  # Lax é mais compatível que Strict
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Configurações CSRF - Segurança aprimorada
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False  # False para permitir leitura via JavaScript se necessário
CSRF_COOKIE_SAMESITE = 'Lax'  # Lax é mais compatível e ainda seguro
CSRF_USE_SESSIONS = False  # Usar cookies ao invés de sessões para melhor compatibilidade
CSRF_FAILURE_VIEW = 'core.error_views.custom_403'  # View personalizada para erro CSRF
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# URLs tolerantes à ausência de barra final
APPEND_SLASH = True

# Configurações de tratamento de erros
handler404 = 'core.error_views.custom_404'
handler500 = 'core.error_views.custom_500'
handler403 = 'core.error_views.custom_403'
handler400 = 'core.error_views.custom_400'

# Propagar exceções apenas em modo debug
DEBUG_PROPAGATE_EXCEPTIONS = DEBUG

# Desabilitar debug toolbar e outras ferramentas de debug que podem interferir
INTERNAL_IPS = []

# ===== CONFIGURAÇÕES FTTH VERIFICADOR =====
# Baseado no Verificador-De-Viabilidade-main

# Diretórios de mapas (criados automaticamente se não existirem)
FTTH_MAPAS_ROOT = BASE_DIR / 'Mapas'
FTTH_KML_DIR = FTTH_MAPAS_ROOT / 'kml'
FTTH_KMZ_DIR = FTTH_MAPAS_ROOT / 'kmz'
FTTH_CSV_DIR = FTTH_MAPAS_ROOT / 'csv'
FTTH_XLS_DIR = FTTH_MAPAS_ROOT / 'xls'
FTTH_XLSX_DIR = FTTH_MAPAS_ROOT / 'xlsx'

# Configurações de roteamento
ROUTING_TIMEOUT = int(os.getenv('ROUTING_TIMEOUT', '15'))  # Timeout em segundos
ENABLE_ROUTE_CACHE = True
MAX_CACHE_SIZE = 1000

# Configurações de viabilidade (distâncias em metros)
FTTH_VIABILIDADE_CONFIG = {
    'viavel': int(os.getenv('VIABILIDADE_VIABLE', '300')),      # Até 300m = Viável
    'limitada': int(os.getenv('VIABILIDADE_LIMITADA', '800')),  # 300-800m = Viabilidade Limitada  
    'inviavel': int(os.getenv('VIABILIDADE_INVIAVEL', '800'))   # Acima de 800m = Sem Viabilidade
}

# OpenRouteService API Key (opcional - para melhor qualidade de roteamento)
OPENROUTESERVICE_API_KEY = os.getenv('OPENROUTESERVICE_API_KEY', '')

# Criar diretórios de mapas se não existirem (apenas se não for test)
import sys
if 'test' not in sys.argv:
    for directory in [FTTH_MAPAS_ROOT, FTTH_KML_DIR, FTTH_KMZ_DIR, FTTH_CSV_DIR, FTTH_XLS_DIR, FTTH_XLSX_DIR]:
        directory.mkdir(parents=True, exist_ok=True)