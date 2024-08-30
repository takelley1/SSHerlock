"""All Django forms for the SSHerlock server application."""
from django.forms import ModelForm

from .models import BastionHost
from .models import Credential
from .models import Job
from .models import LlmApi
from .models import TargetHost


class CredentialForm(ModelForm):
    """Present a form matching the Credential model."""

    class Meta:
        model = Credential
        fields = ["credential_name", "user", "username", "password"]


class BastionHostForm(ModelForm):
    """Present a form matching the Bastion Host model."""

    class Meta:
        model = BastionHost
        fields = ["hostname", "user"]


class TargetHostForm(ModelForm):
    """Present a form matching the Target Host model."""

    class Meta:
        model = TargetHost
        fields = ["hostname", "user"]


class LlmApiForm(ModelForm):
    """Present a form matching the LLM API model."""

    class Meta:
        model = LlmApi
        fields = ["base_url", "api_key", "user"]


class JobForm(ModelForm):
    """Present a form matching the Job model."""

    class Meta:
        model = Job
        fields = [
            "llm_api",
            "bastion_host",
            "credentials_for_bastion_host",
            "target_hosts",
            "credentials_for_target_hosts",
            "instructions",
            "user",
        ]
