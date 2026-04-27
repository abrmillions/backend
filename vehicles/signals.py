from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Vehicle
from applications.models import Notification

User = get_user_model()

@receiver(post_save, sender=Vehicle)
def notify_admin_on_vehicle_registration(sender, instance, created, **kwargs):
    """
    Notify admins when a new vehicle is registered.
    """
    if created:
        admins = User.objects.filter(is_superuser=True, is_active=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="New Vehicle Registered",
                message=f"A new vehicle has been registered by {instance.owner.email}."
            )
