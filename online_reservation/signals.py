from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import Patient, Doctor, Comment


User = get_user_model()


@receiver(post_save, sender=User)
def create_patient_for_newly_created_user(sender, instance, created, **kwargs):
    if created:
        Patient.objects.create(user=instance)


@receiver(post_save, sender=Comment)
def remove_comment_for_change_status_to_not_approved(sender, instance, **kwargs):
    if instance.status == Comment.COMMENT_STATUS_NOT_APPROVED:
        instance.delete()


@receiver(post_save, sender=Doctor)
def remove_doctor_for_change_status_to_rejected(sender, instance, **kwargs):
    if instance.status == Doctor.DOCTOR_STATUS_REJECTED:
        instance.delete()
