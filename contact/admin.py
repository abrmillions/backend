from django.contrib import admin
from .models import ContactMessage, ContactReply


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "subject", "status", "created_at")
    search_fields = ("email", "subject", "message", "name")
    list_filter = ("status", "created_at")


@admin.register(ContactReply)
class ContactReplyAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "sender_type", "created_at")
    search_fields = ("text",)
