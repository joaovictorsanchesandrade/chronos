from django.utils.translation import gettext as _
from rest_framework import serializers
from apps.common.models import Business, Employee, TimeRecord, WorkSession
from typing import Any, Optional


class BusinessSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    allowed_ips = serializers.ListField(
        child=serializers.IPAddressField(), required=False, allow_empty=True
    )

    class Meta:
        model = Business
        fields = (
            "public_uuid",
            "picture",
            "allowed_ips",
            "restricted_network",
            "allowed_radius_meters",
            "lat",
            "lng",
            "restricted_gps",
            "short_link",
            "name",
            "summary",
            "description",
            "updated_at",
            "created_at",
            "owner",
        )
        read_only_fields = ("public_uuid", "updated_at", "created_at", "short_link")

    def validate(self, attrs: dict[str, Any]):
        attrs = super().validate(attrs)
        restricted_gps = attrs["restricted_gps"]
        if restricted_gps:
            lat, lng = attrs.get("lat"), attrs.get("lng")
            if lat is None or lng is None:
                raise serializers.ValidationError(
                    _(
                        "Latitude e longitude são obrigatórias quando a restrição de localização por GPS estiver ativa."
                    )
                )
        return attrs


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = (
            "public_uuid",
            "picture",
            "register",
            "pin",
            "is_active",
            "name",
            "updated_at",
            "created_at",
        )
        read_only_fields = ("public_uuid", "pin", "updated_at", "created_at")

    def validate_register(self, value: str):
        business = self.context["business"]
        _instance: Optional[Employee] = self.instance
        if _instance and _instance.register == value:
            return value
        
        queryset = Employee.objects.filter(register=value, business=business)
        if queryset.exists():
            raise serializers.ValidationError(
                _("O código de registro do funcionário já existe.")
            )
        return value

    def create(self, validated_data):
        business = self.context["business"]
        return Employee.objects.create(business=business, **validated_data)


class TimeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeRecord
        fields = (
            "type",
            "ajusted_at",
            "adjustment_reason",
            "client_ip",
            "registred_at",
        )
        read_only_fields = ("type", "client_ip", "registred_at")


class WorkSessionSerializer(serializers.ModelSerializer):
    time_records = TimeRecordSerializer(many=True)

    class Meta:
        model = WorkSession
        fields = (
            "start_at",
            "end_at",
            "is_edited",
            "edit_reason",
            "trusted",
            "created_at",
            "updated_at",
            "time_records",
        )
        read_only_fields = (
            "start_at",
            "end_at",
            "is_edited",
            "created_at",
            "updated_at",
        )
