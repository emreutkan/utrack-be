from django.contrib import admin
from .models import CustomUser, UserProfile, SecurityStatus, Preferences

admin.site.register(CustomUser)
admin.site.register(UserProfile)
admin.site.register(SecurityStatus)
admin.site.register(Preferences)
