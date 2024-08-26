"""All Django app configs for the SSHerlock server application."""
from django.apps import AppConfig


class SsherlockServerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ssherlock_server"
