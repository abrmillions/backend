from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Application, Notification
from .notifications import send_application_notification
from contact.models import ContactMessage

User = get_user_model()

@receiver(pre_save, sender=Application)
def track_status_change(sender, instance, **kwargs):
    """
    Store the original status of an application before it is saved.
    """
    if instance.pk:
        try:
            old_instance = Application.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Application.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Application)
def handle_application_status_change(sender, instance, created, **kwargs):
    """
    Signal to automatically send notifications when an application status changes.
    """
    if created:
        # Send "Received" notification to applicant
        send_application_notification(instance, "received")
        
        # Notify admins about new application
        admins = User.objects.filter(is_superuser=True, is_active=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                application=instance,
                title="New License Application",
                message=f"A new {instance.license_type} has been submitted by {instance.applicant.email}."
            )
    else:
        # Check if status has changed
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            # Status has changed!
            send_application_notification(instance, instance.status)

@receiver(post_save, sender=User)
def notify_admin_on_registration(sender, instance, created, **kwargs):
    """
    Notify admins when a new user registers.
    """
    if created and not instance.is_superuser:
        admins = User.objects.filter(is_superuser=True, is_active=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="New User Registration",
                message=f"A new user {instance.email} has registered as an {instance.role}."
            )

@receiver(post_save, sender=ContactMessage)
def notify_admin_on_contact_message(sender, instance, created, **kwargs):
    """
    Notify admins when a new contact message is received.
    """
    if created:
        admins = User.objects.filter(is_superuser=True, is_active=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="New Contact Message",
                message=f"New message from {instance.name} ({instance.email}): {instance.subject[:50]}..."
            )

