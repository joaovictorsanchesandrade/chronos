from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext as _


class ApplicationException(APIException):
    default_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _("Ocorreu um erro interno no aplicativo.")
