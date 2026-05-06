from django.contrib import admin
from apps.common.models import Business, Employee, WorkSession, TimeRecord

admin.site.register(Business)
admin.site.register(Employee)
admin.site.register(WorkSession)
admin.site.register(TimeRecord)
