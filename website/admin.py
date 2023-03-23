from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from rest_framework.authtoken.admin import TokenAdmin

from .models import Physician, Scan, Report, Microscope, Patient, Doctor, Department, ScheduledTask, SPMonitor, \
    SPMachine, SPSample, SPAlert

# for rest framework token scheme
TokenAdmin.raw_id_fields = ['user']


# Define an inline admin descriptor for Physician model
# which acts a bit like a singleton
class PhysicianInline(admin.StackedInline):
    model = Physician
    can_delete = False
    verbose_name_plural = 'physician'


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (PhysicianInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Physician)
admin.site.register(Scan)
admin.site.register(Report)
admin.site.register(Microscope)
admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(Department)
admin.site.register(SPMonitor)
admin.site.register(SPMachine)
admin.site.register(SPSample)
admin.site.register(SPAlert)
