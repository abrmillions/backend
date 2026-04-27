from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Partnership, PartnershipApprovalLog
from applications.models import Notification

User = get_user_model()

@receiver(pre_save, sender=Partnership)
def partnership_pre_save(sender, instance: Partnership, **kwargs):
    try:
        if instance.end_date and instance.end_date < timezone.localdate():
            if instance.status in {"approved", "active"}:
                instance.status = "expired"
    except Exception:
        pass

@receiver(post_save, sender=Partnership)
def partnership_post_save(sender, instance: Partnership, created, **kwargs):
    try:
        if created:
            # Notify admins about new partnership registration
            admins = User.objects.filter(is_superuser=True, is_active=True)
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    title="New Partnership Registered",
                    message=f"A new {instance.get_partnership_type_display()} has been registered by {instance.owner.email}."
                )

        # Simple notification stub for expiration
        if instance.status == "expired":
            print(f"[notify] Partnership {instance.id} expired")
    except Exception as e:
        print(f"Error in partnership_post_save signal: {str(e)}")
