from django.utils.translation import gettext as _


class ApplicationException(Exception):
    """The base exception for all application exceptions."""

    def __init__(
        self, detail: str = _("Ocorreu um erro interno"), status_code: int = 500
    ):
        self.detail = detail
        self.status_code = status_code
