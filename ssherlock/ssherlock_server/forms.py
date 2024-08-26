from django.forms import ModelForm
from .models import *


class AddCredentialForm(ModelForm):
    class Meta:
        model = Credential
        fields = ["credential_name", "username", "password"]
