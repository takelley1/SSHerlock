"""All Django forms for the SSHerlock server application."""
from django.forms import ModelForm

from .models import Credential


class CredentialForm(ModelForm):
    """Present a form matching the Credential model."""

    class Meta:
        model = Credential
        fields = ["credential_name", "user", "username", "password"]


class BastionHostForm(ModelForm):
    """Present a form matching the Bastion Host model."""


class TargetHostForm(ModelForm):
    """Present a form matching the Target Host model."""
