from django.utils.translation import gettext as _

from config.celery_config import app
from .models import Reserve


@app.task(queue='tasks')
def remove_patient_from_reserve_after_expired(reserve_id):
    try:
        reserve = Reserve.objects.get(id=reserve_id)
        if reserve.patient and reserve.status == Reserve.RESERVE_STATUS_UNPAID:
            reserve.patient = None
            reserve.save()
            return _('The patient was successfully removed from the reserve.')
        return _('No patient had this reserve.')
    except Reserve.DoesNotExist:
        return _("There isn't any reserve with id={reserve_id}." % {'reserve_id': reserve_id})
