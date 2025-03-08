from django.contrib import admin
from .models import User, LoginHistory

admin.site.register(User)
admin.site.register(LoginHistory)

