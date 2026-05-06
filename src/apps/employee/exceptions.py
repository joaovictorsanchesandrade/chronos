from apps.common.exceptions import ApplicationException


class EmployeeException(ApplicationException):
    """Exception base for all exceptions in the employee module."""


class InvalidTimeRecordException(ApplicationException):
    """Invalid time record type"""

    def __init__(self, detail=..., status_code=400):
        super().__init__(detail, status_code)
