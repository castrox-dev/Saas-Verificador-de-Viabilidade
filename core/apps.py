from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Importar signals para notificações de tickets
        import core.ticket_signals  # noqa: F401
        
        # Ao habilitar o controle de sessão única:
        # import core.signals_single_session  # noqa: F401
