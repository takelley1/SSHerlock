"""All Django admin configs for the SSHerlock server application."""
from django.contrib import admin

from .models import *

admin.site.register(BastionHost)
admin.site.register(Credential)
admin.site.register(Job)
admin.site.register(LlmApi)
admin.site.register(TargetHost)
admin.site.register(User)
