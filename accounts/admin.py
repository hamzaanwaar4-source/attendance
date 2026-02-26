from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ["email", "username", "is_active", "is_staff"]
    ordering = ["-date_joined"]


admin.site.register(CustomUser, CustomUserAdmin)
