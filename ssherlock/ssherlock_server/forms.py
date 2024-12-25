"""All Django forms for the SSHerlock server application."""

# pylint: disable=import-error, missing-class-docstring
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from .models import BastionHost
from .models import Credential
from .models import Job
from .models import LlmApi
from .models import TargetHost


class CustomUserCreationForm(UserCreationForm):
    """Present a customized user creation form that allows us to set the user's email."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        """Save the user instance with the email."""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class CredentialForm(ModelForm):
    """Form for creating and updating Credential instances."""

    class Meta:
        model = Credential
        fields = ["credential_name", "username", "password"]
        widgets = {
            "credential_name": forms.TextInput(
                attrs={
                    "class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"
                }
            ),
            "username": forms.TextInput(
                attrs={
                    "class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"
                }
            ),
            "password": forms.PasswordInput(
                attrs={
                    "class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"
                }
            ),
        }


class BastionHostForm(ModelForm):
    """Form for creating and updating BastionHost instances."""

    port = forms.IntegerField(
        initial=22,
        widget=forms.NumberInput(
            attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}
        ),
    )

    class Meta:
        model = BastionHost
        fields = ["hostname", "port"]
        widgets = {
            "hostname": forms.TextInput(
                attrs={
                    "class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"
                }
            ),
        }


class TargetHostForm(ModelForm):
    """Form for creating and updating TargetHost instances."""

    port = forms.IntegerField(
        initial=22,
        widget=forms.NumberInput(
            attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}
        ),
    )

    class Meta:
        model = TargetHost
        fields = ["hostname", "port"]
        widgets = {
            "hostname": forms.TextInput(
                attrs={
                    "class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"
                }
            ),
        }


class LlmApiForm(ModelForm):
    """Form for creating and updating LlmApi instances."""

    class Meta:
        model = LlmApi
        fields = ["base_url", "api_key"]
        widgets = {
            "base_url": forms.URLInput(
                attrs={
                    "class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"
                }
            ),
            "api_key": forms.TextInput(
                attrs={
                    "class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"
                }
            ),
        }


class JobForm(ModelForm):
    """Form for creating and updating Job instances."""

    instructions = forms.CharField(
        max_length=128000,
        help_text="Instructions for the job, limited to 128,000 characters.",
        widget=forms.Textarea(
            attrs={"class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"}
        ),
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
        ]
        widgets = {
            "llm_api": forms.Select(
                attrs={
                    "class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"
                }
            ),
            "bastion_host": forms.Select(
                attrs={
                    "class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"
                }
            ),
            "credentials_for_bastion_host": forms.Select(
                attrs={
                    "class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"
                }
            ),
            "target_hosts": forms.SelectMultiple(
                attrs={
                    "class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"
                }
            ),
            "credentials_for_target_hosts": forms.Select(
                attrs={
                    "class": "text-white bg-gray-700 p-2 border border-gray-600 rounded"
                }
            ),
        }
