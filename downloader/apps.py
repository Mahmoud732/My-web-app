from django.apps import AppConfig


class DownloaderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'downloader'
    def ready(self):
        import downloader.signals  # Make sure the signals are connected
