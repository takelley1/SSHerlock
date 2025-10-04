"""Django admin registrations for SSHerlock."""
# pylint: disable=import-error
from django.contrib import admin

from .models import BastionHost, Credential, Job, LlmApi, TargetHost


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    """Credential admin: do not expose private keys in lists."""

    list_display = ("credential_name", "username", "credential_type", "created_at")
    readonly_fields = ("created_at",)
    fieldsets = (
        (None, {"fields": ("credential_name", "credential_type", "username", "password", "private_key")}),
        ("Meta", {"fields": ("created_at",)}),
    )


admin.site.register(BastionHost)
admin.site.register(Job)
admin.site.register(LlmApi)
admin.site.register(TargetHost)
