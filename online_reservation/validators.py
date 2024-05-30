from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class NationalCodeValidator(RegexValidator):
    regex = r'^[1-9][0-9]{9}$'
    message = _(
        'Enter a valid national code, National code must be 10 digits'
        ' which start with one of the numbers between 1 and 9.'
    )
    code = 'invalid_national_code'


class MedicalCouncilNumberValidator(RegexValidator):
    regex = r'^[1-9][0-9]{4}$'
    message = _(
        'Enter a valid medical council number, Medical council number must be 5 digits'
        ' which start with one of the numbers between 1 and 9.'
    )
    code = 'invalid_medical_council_number'
