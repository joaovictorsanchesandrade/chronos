from rest_framework import serializers
from apps.common.models import (
    TimeRecordType,
    Employee,
    WorkSession,
    TimeRecord,
    Business,
)
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


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ("picture", "name", "summary")


class EmployeeSerializer(serializers.ModelSerializer):
    business = BusinessSerializer()

    class Meta:
        model = Employee
        fields = ("picture", "register", "name", "business")


class TimeRecordsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeRecord
        fields = (
            "type",
            "client_ip",
            "registred_at",
            "location_lat",
            "location_lng",
            "location_accuracy",
            "distance_from_business_meters"
        )
        

class WorkSessionSerializer(serializers.ModelSerializer):
    time_records = TimeRecordsSerializer(many=True)

    class Meta:
        model = WorkSession
        fields = ("start_at", "time_records")
