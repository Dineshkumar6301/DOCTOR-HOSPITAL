from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Clinic

User = get_user_model()

@receiver(post_save, sender=User)
def create_clinic_for_superuser(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        full_name = f"{instance.first_name} {instance.last_name}".strip()

        if not Clinic.objects.filter(name__iexact=full_name).exists():
            Clinic.objects.create(
                name=full_name,
                address="",
                admin=instance
            )
