from django.utils.translation import gettext as _
from rest_framework.validators import ValidationError
from geopy.distance import geodesic
import ipaddress


def validate_location(
    *,
    position_check: tuple[float, float, int | None],
    position_valid: tuple[float, float],
    allowed_radius_meters: int,
) -> tuple[bool, float | None]:
    """Check if the entered location is within the permitted area."""

    lat, log, accurancy = position_check
    distance = geodesic((lat, log), position_valid).meters

    if accurancy and accurancy > 80:
        return False, None

    return distance <= allowed_radius_meters, distance


def validate_network(*, ip_check: str, allowed_ips: list[str]):
    """Check if the provided IP address is within the allowed IP addresses."""
    client_ip = ipaddress.ip_address(ip_check)
    for allowed_ip in allowed_ips:
        if client_ip == ipaddress.ip_address(allowed_ip):
            return True
    return False
