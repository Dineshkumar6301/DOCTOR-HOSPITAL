

from django.apps import AppConfig

class DiagnosisConfig(AppConfig):
    name = 'pharmacy'

    def ready(self):
        import pharmacy.signals
