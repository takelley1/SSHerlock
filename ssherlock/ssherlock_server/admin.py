"""All Django admin configs for the SSHerlock server application."""
# pylint: disable=import-error
from django.contrib import admin

from .models import BastionHost
from .models import Credential
from .models import Job
from .models import LlmApi
from .models import TargetHost
from .models import User

admin.site.register(BastionHost)
admin.site.register(Credential)
admin.site.register(Job)
admin.site.register(LlmApi)
admin.site.register(TargetHost)
admin.site.register(User)
