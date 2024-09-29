from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model

from datetime import timezone, timedelta, datetime

from .models import Patient, Doctor, Comment, Reserve
from .tasks import remove_patient_from_reserve_after_expired


TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))
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


@receiver(post_save, sender=Reserve)
def manage_patient_for_newly_reserve(sender, instance, created, **kwargs):
    if created and instance.reserve_datetime > datetime.now(tz=TEHRAN_TZ):
        eta = instance.reserve_datetime
        remove_patient_from_reserve_after_expired.apply_async((instance.id, ), eta=eta)