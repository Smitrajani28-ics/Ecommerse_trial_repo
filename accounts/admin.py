from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Address


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['phone', 'date_of_birth', 'avatar', 'bio', 'newsletter_subscription', 'email_notifications']


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ['type', 'first_name', 'last_name', 'city', 'state', 'is_default', 'is_active']
    readonly_fields = ['created_at']


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline, AddressInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'newsletter_subscription', 'email_notifications', 'created_at']
    list_filter = ['newsletter_subscription', 'email_notifications', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'full_name', 'city', 'state', 'is_default', 'is_active']
    list_filter = ['type', 'is_default', 'is_active', 'country', 'created_at']
    search_fields = ['user__username', 'first_name', 'last_name', 'city', 'state']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'type', 'is_default', 'is_active')
        }),
        ('Personal Details', {
            'fields': ('first_name', 'last_name', 'company', 'phone')
        }),
        ('Address', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
