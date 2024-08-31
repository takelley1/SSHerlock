"""All Django app configs for the SSHerlock server application."""
# pylint: disable=import-error
from django.apps import AppConfig


class SsherlockServerConfig(AppConfig):
    """Main app configuration for SSHerlock Server."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "ssherlock_server"
