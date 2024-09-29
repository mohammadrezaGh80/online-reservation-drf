from django.utils.translation import gettext as _

from config.celery_config import app
from .models import Reserve


@app.task(queue='tasks')
def remove_patient_from_reserve_after_expired(reserve_id):
    try:
        reserve = Reserve.objects.get(id=reserve_id)
        patient = reserve.patient
        if reserve.status == Reserve.RESERVE_STATUS_UNPAID:
            if reserve.patient:
                reserve.patient = None
                reserve.save()
                return _('%(patient_fullname)s was successfully removed from the reserve.' % {'patient_fullname': patient.full_name})
            return _('No patient had this reserve.')
        return _('%(patient_fullname)s has successfully taken the reserve.' % {'patient_fullname': patient.full_name})
    except Reserve.DoesNotExist:
        return _("There isn't any reserve with id=%(reserve_id)d." % {'reserve_id': reserve_id})


@app.task(queue='tasks')
def manage_patient_after_end_of_reserve_purchase_time(reserve_id):
    try:
        reserve = Reserve.objects.get(id=reserve_id)
        patient = reserve.patient
        if reserve.status == Reserve.RESERVE_STATUS_UNPAID:
            reserve.patient = None
            reserve.celery_task_id = ''
            reserve.celery_payment_expiration_datetime = None
            reserve.save(update_fields=['patient', 'celery_task_id', 'celery_payment_expiration_datetime'])
            return _('Purchase time is finish, %(patient_fullname)s was successfully removed from the reserve.' % {'patient_fullname': patient.full_name})
        return _('%(patient_fullname)s has successfully taken the reserve.' % {'patient_fullname': patient.full_name})
    except Reserve.DoesNotExist:
        return _("There isn't any reserve with id=%(reserve_id)d." % {'reserve_id': reserve_id})
