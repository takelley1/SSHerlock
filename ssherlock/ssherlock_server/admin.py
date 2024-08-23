from django.contrib import admin

from .models import *

admin.site.register(User)
admin.site.register(TargetServer)
admin.site.register(Credential)
admin.site.register(LlmApi)
