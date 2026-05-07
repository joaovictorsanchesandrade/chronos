from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _
from apps.common.querysets import (
    BusinessQuerySet,
    EmployeeQuerySet,
)
from uuid import uuid4
import string
import random
import ipaddress


def upload_photo(instance: models.Model, filename: str) -> str:
    """Creates a relative path for the model image."""
    class_name = instance.__class__.__name__.lower()
    return f"{class_name}/pictures/{filename}"


def random_pin(length: int = 5) -> str:
    """Generates a random pin."""
    return "".join(random.choice(string.digits) for _ in range(length))


def random_code(length: int = 8) -> str:
    """Generates a random alphanumeric code"""
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


class TimeRecordType(models.TextChoices):
    ENTRY = "entry", _("Entrada")
    BREAK_START = "break_start", _("Inicio do Intervalo")
    BREAK_END = "break_end", _("Fim do Intervalo")
    EXIT = "exit", _("Saida")


class BaseModel(models.Model):
    """
    Abstract base of the models we will use
    in these classes, to standardize some fields
    that we will use in all models.
    """

    public_uuid = models.URLField(
        _("identificador publico"),
        default=uuid4,
        unique=True,
        db_index=True,
        editable=False,
    )
    picture = models.ImageField(
        _("foto"), upload_to=upload_photo, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """It ensures that if the user updates the photo, the old one will be deleted."""
        if self.pk:
            old = type(self).objects.filter(pk=self.pk).first()
            if old and old.picture and old.picture != self.picture:
                old.picture.delete(save=False)

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """It guarantees that the image will be deleted."""
        if self.picture:
            self.picture.delete(save=False)
        return super().delete(*args, **kwargs)

    def user_delete(self):
        """The user is deleting the model; we only updated the model to perform the controlled deletion."""
        self.is_deleted = True
        self.is_active = False
        self.save()


class Business(BaseModel):
    objects = BusinessQuerySet.as_manager()

    name = models.CharField(_("nome"), max_length=256)
    summary = models.CharField(_("resumo"), max_length=512, blank=True, null=True)
    description = models.TextField(_("descrição"), blank=True, null=True)
    allowed_ips = models.JSONField(_("IPs liberados"), default=list, blank=True)
    all_network = models.BooleanField(_("Qualquer rede"), default=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="businesses",
        db_index=True,
        verbose_name=_("proprietário"),
    )
    short_link = models.CharField(null=True, blank=True)

    class Meta:
        db_table = "core_businesses"
        verbose_name = _("empresa")
        verbose_name_plural = _("empresas")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["owner", "created_at"]),
            models.Index(fields=["is_deleted", "owner"]),
            models.Index(fields=["is_deleted", "owner", "public_uuid"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.short_link:
            while 1:
                short_link = random_code()
                queryset = Business.objects.filter(short_link=short_link)
                if queryset.exists():
                    continue
                self.short_link = short_link
                break
        return super().save(*args, **kwargs)

    def ip_is_allowed(self, ip: str) -> bool:
        """Check if the employee has permission to access the site from that IP address."""
        if self.all_network:
            return True

        client_ip = ipaddress.ip_address(ip)
        for allowed_ip in self.allowed_ips:
            if client_ip == ipaddress.ip_address(allowed_ip):
                return True
        return False


class Employee(BaseModel):
    objects = EmployeeQuerySet.as_manager()

    register = models.CharField(_("registro"), max_length=256)
    pin = models.CharField(_("PIN"), default=random_pin, max_length=20)
    name = models.CharField(_("nome"), max_length=256)
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="employees",
        verbose_name=_("empresa"),
    )

    class Meta:
        db_table = "core_employees"
        verbose_name = _("funcionário")
        verbose_name_plural = _("funcionários")
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["business", "register"],
                name="unique_employee_register_per_business",
            )
        ]
        indexes = [
            models.Index(fields=["business", "is_active"]),
        ]


class WorkSession(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="work_sessions",
        verbose_name=_("Funcionário"),
    )

    start_at = models.DateTimeField(_("Iniciou em"), blank=False, null=False)
    end_at = models.DateTimeField(_("Terminou em"), blank=True, null=True)

    is_edited = models.BooleanField(_("Foi editado"), default=False)
    edit_reason = models.CharField(
        _("Motivo da edição"), max_length=512, blank=True, null=True
    )

    trusted = models.BooleanField(_("Confiável"), default=True)

    created_at = models.DateTimeField(_("Criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Atualizado em "), auto_now=True)

    class Meta:
        db_table = "core_work_sessions"


class TimeRecord(models.Model):
    work_session = models.ForeignKey(
        WorkSession,
        on_delete=models.CASCADE,
        related_name="time_records",
        verbose_name=_("Jornada"),
    )
    type = models.CharField(
        _("Tipo"),
        max_length=32,
        choices=TimeRecordType.choices,
    )
    ajusted_at = models.DateTimeField(_("Horário Ajustado"), null=True, blank=True)
    adjustment_reason = models.CharField(
        _("Motivo do ajuste"), max_length=512, null=True, blank=True
    )
    client_ip = models.GenericIPAddressField(_("IP do cliente"), null=True, blank=True)
    registred_at = models.DateTimeField(_("Registrado em"), auto_now_add=True)

    class Meta:
        db_table = "core_time_records"
