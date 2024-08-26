"""All Django forms for the SSHerlock server application."""
from django.forms import ModelForm

from .models import Credential


class CredentialForm(ModelForm):
    class Meta:
        model = Credential
        fields = ["credential_name", "user", "username", "password"]
