from django.contrib.auth.models import User
from rest_framework import serializers

from website.drf_writable_nested import WritableNestedModelSerializer
from website.models import Physician, Microscope, Scan, Report, Patient, Doctor, Department, ScheduledTask, SPMonitor, \
    SPMachine, SPSample, SPAlert, Action, SPLog, Specimen, UserDefined


class UserDefinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDefined
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=200, allow_blank=True, required=False)
    password = serializers.CharField(max_length=200, allow_blank=True, required=False)

    class Meta:
        model = User
        fields = '__all__'


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = '__all__'


class PhysicianSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=False)

    class Meta:
        model = Physician
        fields = '__all__'
        depth = 1

    def create(self, validated_data):
        user = validated_data.pop('user')
        user = User.objects.create_user(**user)
        physician = Physician.objects.create(user=user, **validated_data)
        return physician

    def update(self, instance, validated_data):
        user = instance.user
        if "user" in validated_data:
            newuser = validated_data.pop("user")
            user.username = newuser.get("username", user.username)
            if "password" in newuser:
                user.set_password(newuser["password"])
            user.save()

        instance.user = user
        super(PhysicianSerializer, self).update(instance, validated_data)
        return instance


class MicroscopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Microscope
        fields = '__all__'


class SpecimenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specimen
        fields = '__all__'


class ScanSerializer(WritableNestedModelSerializer):
    occupied_by = UserSerializer(required=False, allow_null=True)
    owner = UserSerializer(required=False, allow_null=True)
    specimen_info = SpecimenSerializer(required=False, allow_null=True)

    class Meta:
        model = Scan
        fields = '__all__'
        depth = 1

    def __init__(self, *args, **kwargs):
        remove_fields = kwargs.pop('remove_fields', None)
        super(ScanSerializer, self).__init__(*args, **kwargs)

        if remove_fields:
            # for multiple fields in a list
            for field_name in remove_fields:
                self.fields.pop(field_name)

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class ScheduledTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledTask
        fields = '__all__'


# sp related
class SPMonitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPMonitor
        fields = '__all__'


class SPMachineSerializer(serializers.ModelSerializer):
    monitor = SPMonitorSerializer(required=False)

    class Meta:
        model = SPMachine
        fields = '__all__'
        depth = 1


class SPSampleSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=False)

    class Meta:
        model = SPSample
        fields = '__all__'

    def to_representation(self, instance):
        self.fields['sp_machine'] = SPMachineSerializer(read_only=True)
        return super().to_representation(instance)


class SPLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPLog
        fields = '__all__'

    def to_representation(self, instance):
        self.fields['sp_machine'] = SPMachineSerializer(read_only=True)
        return super().to_representation(instance)


class SPAlertSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=False)

    class Meta:
        model = SPAlert
        fields = '__all__'

    def to_representation(self, instance):
        self.fields['sp_machine'] = SPMachineSerializer(read_only=True)
        return super().to_representation(instance)
