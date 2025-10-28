from django.apps import AppConfig


class VerificadorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'verificador'
    verbose_name = 'Verificador de Viabilidade'
    
    def ready(self):
        """Configurações iniciais do app"""
        pass
