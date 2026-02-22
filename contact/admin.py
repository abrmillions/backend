from django.contrib import admin
from django.core.mail import EmailMultiAlternatives, get_connection
from .models import ContactMessage, ContactReply
from systemsettings.models import SystemSettings


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "subject", "status", "created_at")
    search_fields = ("email", "subject", "message")
    list_filter = ("status", "created_at")


@admin.register(ContactReply)
class ContactReplyAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "sender_type", "created_at")
    search_fields = ("text",)
    list_filter = ("sender_type", "created_at")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            if change:
                return
            settings_obj = SystemSettings.get_solo()
            if not getattr(settings_obj, "email_notifications", True):
                return
            host = getattr(settings_obj, "smtp_host", "") or ""
            port = int(getattr(settings_obj, "smtp_port", 587) or 587)
            user = getattr(settings_obj, "smtp_user", "") or ""
            password = getattr(settings_obj, "smtp_password", "") or ""
            use_tls = bool(getattr(settings_obj, "use_tls", True))
            if not (host and user and obj.message and obj.message.email):
                return
            connection = get_connection(
                host=host,
                port=port,
                username=user,
                password=password,
                use_tls=use_tls,
            )
            subject = f"Reply to your message: {obj.message.subject or 'No subject'}"
            admin_name = getattr(getattr(request, "user", None), "get_full_name", lambda: "")() or getattr(request.user, "email", "") or "Admin"
            body = (
                f"Hello {obj.message.name},\n\n"
                f"Our team has replied to your message:\n\n"
                f"{obj.text.strip()}\n\n"
                f"— {admin_name}\n"
                f"{getattr(settings_obj, 'system_name', 'Construction License Management System')}"
            )
            email = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=user,
                to=[obj.message.email],
                reply_to=[getattr(settings_obj, "support_email", user) or user],
                connection=connection,
            )
            email.send(fail_silently=True)
        except Exception:
            pass
