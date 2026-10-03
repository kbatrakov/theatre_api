from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from user.models import User


class CustomUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'full_name', 'is_staff', 'is_active')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')
        }),
    )

admin.site.register(User, CustomUserAdmin)
