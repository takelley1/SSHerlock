from django.contrib import admin

from .models import *

admin.site.register(BastionServer)
admin.site.register(Credential)
admin.site.register(Job)
admin.site.register(LlmApi)
admin.site.register(TargetServer)
admin.site.register(User)
