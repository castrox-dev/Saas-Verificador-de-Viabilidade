from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    # Ao habilitar o controle de sessão única:
    # def ready(self):
    #     import core.signals_single_session  # noqa: F401
