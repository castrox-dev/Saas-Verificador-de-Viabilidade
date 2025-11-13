from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "on", "yes")
ALLOWED_HOSTS_ENV = os.getenv("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_ENV.split(",") if h.strip()] or ["127.0.0.1", "localhost", "testserver", "*"]

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

requires_ssl = not DATABASE_URL.startswith("postgresql://localhost") and not DATABASE_URL.startswith("postgres://localhost")

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
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/rm/login/"
LOGIN_URL = "/rm/login/"

# Custom User Model
AUTH_USER_MODEL = 'core.CustomUser'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CSRF and cookie security
CSRF_TRUSTED_ORIGINS_ENV = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in CSRF_TRUSTED_ORIGINS_ENV.split(",") if o.strip()]

# Se não houver CSRF_TRUSTED_ORIGINS configurado, adicionar hosts permitidos automaticamente
if not CSRF_TRUSTED_ORIGINS:
    # Adicionar https:// para cada host permitido (exceto wildcard)
    for host in ALLOWED_HOSTS:
        if host and host != '*':
            # Adicionar com e sem www
            origin = f"https://{host}"
            if origin not in CSRF_TRUSTED_ORIGINS:
                CSRF_TRUSTED_ORIGINS.append(origin)
            if not host.startswith('www.'):
                origin_www = f"https://www.{host}"
                if origin_www not in CSRF_TRUSTED_ORIGINS:
                    CSRF_TRUSTED_ORIGINS.append(origin_www)
    
    # Se ainda estiver vazio e estiver em produção, adicionar domínios comuns do Railway
    if not CSRF_TRUSTED_ORIGINS and not DEBUG:
        # Tentar detectar domínio do Railway através de variáveis de ambiente
        railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
        if railway_public_domain:
            origin = f"https://{railway_public_domain}"
            if origin not in CSRF_TRUSTED_ORIGINS:
                CSRF_TRUSTED_ORIGINS.append(origin)
        
        # Adicionar domínio específico do Railway se detectado
        # O Railway geralmente usa *.up.railway.app, mas precisamos do domínio exato
        # Por isso é importante configurar CSRF_TRUSTED_ORIGINS manualmente

# Log para debug (apenas em desenvolvimento)
if DEBUG:
    print(f"CSRF_TRUSTED_ORIGINS: {CSRF_TRUSTED_ORIGINS}")
    print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")

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