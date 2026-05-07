from django.utils import timezone
from django.utils.translation import gettext as _
from apps.common.models import (
    Employee,
    WorkSession,
    TimeRecord,
    TimeRecordType,
)
from apps.common.types import ClientLocation
from apps.employee.exceptions import (
    InvalidTimeRecordException,
)
from typing import Optional


def get_work_session(*, employee: Employee, record_type: TimeRecordType) -> WorkSession:
    """Returns to the session the employee is currently in."""
    if record_type == TimeRecordType.ENTRY:
        return WorkSession.objects.create(employee=employee, start_at=timezone.now())
    work_session = WorkSession.objects.filter(employee=employee).last()
    if record_type == TimeRecordType.EXIT:
        work_session.end_at = timezone.now()
        work_session.save(update_fields=["end_at"])
    return work_session


def create_time_record(
    *,
    employee: Employee,
    record_type: TimeRecordType,
    client_ip: str,
    client_location: ClientLocation,
) -> TimeRecord:
    """Creates a time record in the database."""
    work_session = get_work_session(employee=employee, record_type=record_type)
    return TimeRecord.objects.create(
        type=record_type,
        client_ip=client_ip,
        work_session=work_session,
        location_lat=client_location.lat,
        location_lng=client_location.lng,
        location_accuracy=client_location.accuracy,
        distance_from_business_meters=client_location.distance,
    )


def get_current_work_session(*, employee: Employee) -> Optional[WorkSession]:
    """Returns to the current work session."""
    return (
        employee.work_sessions.filter(end_at__isnull=True)
        .prefetch_related("time_records")
        .first()
    )


def validate_time_record(*, employee: Employee, record_type: str):
    """Validates whether the time record created by the user is valid."""
    open_session: Optional[WorkSession] = get_current_work_session(employee=employee)
    if record_type == TimeRecordType.ENTRY:
        if open_session:
            raise InvalidTimeRecordException(_("Já existe uma sessão aberta"))
        return

    if not open_session:
        raise InvalidTimeRecordException(_("Nenhuma jornada aberta foi encotrada."))

    last_record: TimeRecord = open_session.time_records.order_by(
        "-registred_at"
    ).first()
    if record_type == TimeRecordType.BREAK_START:
        if (
            last_record.type == TimeRecordType.ENTRY
            or last_record.type == TimeRecordType.BREAK_END
        ):
            return
        raise InvalidTimeRecordException(_("Não é possivel inicia uma pausa agora."))

    if record_type == TimeRecordType.BREAK_END:
        if last_record.type == TimeRecordType.BREAK_START:
            return
        raise InvalidTimeRecordException(_("Não existe uma pausa em andamento."))

    if record_type == TimeRecordType.EXIT:
        if last_record.type == TimeRecordType.BREAK_START:
            raise InvalidTimeRecordException(
                _("Não é possivel finalizar durante uma pausa.")
            )

        if last_record.type in [TimeRecordType.ENTRY, TimeRecordType.BREAK_END]:
            return
        raise _("Não é possivel finalizar a jornada agora.")
