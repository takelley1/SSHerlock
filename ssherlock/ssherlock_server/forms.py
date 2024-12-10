"""All Django forms for the SSHerlock server application."""

# pylint: disable=import-error, missing-class-docstring
from django.forms import ModelForm
from django import forms

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
        widgets = {
            "credential_name": forms.TextInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
            "user": forms.TextInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
            "username": forms.TextInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
            "password": forms.PasswordInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
        }


class BastionHostForm(ModelForm):
    """Present a form matching the Bastion Host model."""

    port = forms.IntegerField(
        initial=22,
        widget=forms.NumberInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"})
    )

    class Meta:
        model = BastionHost
        fields = ["hostname", "user", "port"]
        widgets = {
            "hostname": forms.TextInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
            "user": forms.TextInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
        }


class TargetHostForm(ModelForm):
    """Present a form matching the Target Host model."""

    port = forms.IntegerField(
        initial=22,
        widget=forms.NumberInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"})
    )

    class Meta:
        model = TargetHost
        fields = ["hostname", "user", "port"]
        widgets = {
            "hostname": forms.TextInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
            "user": forms.TextInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
        }


class LlmApiForm(ModelForm):
    """Present a form matching the LLM API model."""

    class Meta:
        model = LlmApi
        fields = ["base_url", "api_key", "user"]
        widgets = {
            "base_url": forms.URLInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
            "api_key": forms.TextInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
            "user": forms.TextInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
        }


class JobForm(ModelForm):
    """Present a form matching the Job model."""

    instructions = forms.CharField(
        max_length=128000,
        help_text="Instructions for the job, limited to 128,000 characters.",
        widget=forms.Textarea(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
    )

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
        widgets = {
            "llm_api": forms.Select(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
            "bastion_host": forms.Select(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
            "credentials_for_bastion_host": forms.Select(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
            "target_hosts": forms.SelectMultiple(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
            "credentials_for_target_hosts": forms.Select(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
            "user": forms.TextInput(attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}),
        }
