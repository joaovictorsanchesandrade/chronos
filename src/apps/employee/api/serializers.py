from rest_framework import serializers
from apps.common.models import TimeRecordType, Employee, WorkSession, TimeRecord
from apps.employee.services import validate_time_record, InvalidTimeRecordException


class ClockingSerializer(serializers.Serializer):
    record_type = serializers.ChoiceField(choices=TimeRecordType.choices)

    def validate(self, attrs):
        employee = self.context["employee"]
        try:
            validate_time_record(employee=employee, record_type=attrs["record_type"])
        except InvalidTimeRecordException as exc:
            raise serializers.ValidationError(exc.detail)
        return attrs


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = (
            "picture",
            "register",
            "name",
        )


class TimeRecordsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeRecord
        fields = (
            "type",
            "client_ip",
            "registred_at",
        )


class WorkSessionSerializer(serializers.ModelSerializer):
    time_records = TimeRecordsSerializer(many=True)

    class Meta:
        model = WorkSession
        fields = ("start_at", "time_records")
