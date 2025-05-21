from django.contrib import admin
from .models import DummyEmailConfiguration, DummyEmailTemplate, EmailLog

# Register your models here.
@admin.register(DummyEmailConfiguration)
class DummyEmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ('email_address', 'is_active', 'daily_limit', 'daily_sent')
    search_fields = ('email_address', 'email_username')
    list_filter = ('is_active',)
    ordering = ('-created_at',)


@admin.register(DummyEmailTemplate)
class DummyEmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('subject',)
    search_fields = ('subject',)
    ordering = ('-created_at',)


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('email_configuration', 'recipient', 'status', 'checked_at')
    search_fields = ('recipient',)
    list_filter = ('status',)
    ordering = ('-checked_at',)
