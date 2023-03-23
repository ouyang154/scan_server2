import base64
import datetime
import json
import logging
import os
import re
import shutil
import subprocess
import traceback
import uuid
from os.path import exists
from typing import List, Tuple

import cv2
import django_filters
import numpy as np
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError, models
from django.utils import timezone
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt
from django_filters import fields
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.widgets import RangeWidget
import requests
from rest_framework import filters, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.status import (HTTP_200_OK, HTTP_202_ACCEPTED,
                                   HTTP_400_BAD_REQUEST,
                                   HTTP_403_FORBIDDEN,
                                   HTTP_404_NOT_FOUND,
                                   HTTP_408_REQUEST_TIMEOUT,
                                   HTTP_500_INTERNAL_SERVER_ERROR)
from rest_framework.views import APIView

from website.models import (Action, Department, Doctor, Microscope, Patient,
                            Physician, Report, Scan, ScheduledTask, SPAlert,
                            Specimen, SPLog, SPMachine, SPMonitor, SPSample,
                            UserDefined)
from website.serializers import (ActionSerializer, DepartmentSerializer,
                                 DoctorSerializer, MicroscopeSerializer,
                                 PatientSerializer, PhysicianSerializer,
                                 ReportSerializer, ScanSerializer,
                                 ScheduledTaskSerializer, SPAlertSerializer,
                                 SpecimenSerializer, SPLogSerializer,
                                 SPMachineSerializer, SPMonitorSerializer,
                                 SPSampleSerializer, UserDefinedSerializer)
from website.utils import (add_bbox_scan, delete_bbox_scan, export_scan,
                           generate_bbox_scan, rm_folder, import_scan,
                           backup_scan_to_path, update_to_be_delete_scan)

logger = logging.getLogger(__name__)


def get_report_config():
    report_config_file = os.path.join(settings.SCAN_SERVER_CONFIG_ROOT, 'scan_server_report_config.json')
    if not os.path.exists(report_config_file):
        # copy default config file
        default_report_config_file = os.path.join(settings.SCAN_SERVER_CONFIG_ROOT, 'scan_server_report_config_default.json')
        shutil.copyfile(default_report_config_file, report_config_file)
    with open(report_config_file, encoding="utf8") as f:
        config_loaded = json.load(f)
    return config_loaded


class RelatedOrderingFilter(filters.OrderingFilter):
    _max_related_depth = 3

    @staticmethod
    def _get_verbose_name(field: models.Field, non_verbose_name: str) -> str:
        return field.verbose_name if hasattr(field, 'verbose_name') else non_verbose_name.replace('_', ' ')

    def _retrieve_all_related_fields(
            self,
            fields: Tuple[models.Field],
            model: models.Model,
            depth: int = 0
    ) -> List[tuple]:
        valid_fields = []
        if depth > self._max_related_depth:
            return valid_fields
        for field in fields:
            if field.related_model and field.related_model != model:
                rel_fields = self._retrieve_all_related_fields(
                    field.related_model._meta.get_fields(),
                    field.related_model,
                    depth + 1
                )
                for rel_field in rel_fields:
                    valid_fields.append((
                        f'{field.name}__{rel_field[0]}',
                        self._get_verbose_name(field, rel_field[1])
                    ))
            else:
                valid_fields.append((
                    field.name,
                    self._get_verbose_name(field, field.name),
                ))
        return valid_fields

    def get_valid_fields(self, queryset: models.QuerySet, view, context: dict = None) -> List[tuple]:
        valid_fields = getattr(view, 'ordering_fields', self.ordering_fields)
        if not valid_fields == '__all_related__':
            if not context:
                context = {}
            valid_fields = super().get_valid_fields(queryset, view, context)
        else:
            valid_fields = [
                *self._retrieve_all_related_fields(queryset.model._meta.get_fields(), queryset.model),
                *[(key, key.title().split('__')) for key in queryset.query.annotations]
            ]
        return valid_fields


@csrf_exempt
@api_view(["POST"])
@permission_classes((AllowAny,))
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if username is None or password is None:
        return Response({'error': 'Please provide both username and password'},
                        status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(username=username, password=password)
    if not user:
        try:
            User.objects.get(username=username)
            return Response({'error': 'Invalid Credentials'},
                            status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({'error': 'No User Found'},
                            status=status.HTTP_404_NOT_FOUND)
    token, _ = Token.objects.get_or_create(user=user)
    physician = Physician.objects.get_or_create(user=user)[0]
    return Response({'token': token.key,
                     'id': user.id},
                    status=HTTP_200_OK)


def grab_cut(image, background_r, foreground_r):
    # image in 1d, turn it to 3d
    raw = np.asarray(image, dtype=np.uint8)
    width = background_r * 2
    raw = raw.reshape(width, width, 3)
    center = (round(raw.shape[1] / 2), round(raw.shape[0] / 2))
    mask = np.zeros_like(raw[..., 0], np.uint8)
    mask = cv2.circle(img=mask, center=center, radius=background_r - 2,
                      color=cv2.GC_PR_BGD, thickness=-1)
    mask = cv2.circle(img=mask, center=center,
                      radius=int(foreground_r),
                      color=cv2.GC_FGD, thickness=-1)
    bm, fm = np.zeros((2, 1, 65))  # trivial parameters just fill places
    cv2.grabCut(raw, mask, (0, 0, 0, 0), bm, fm, 6, cv2.GC_INIT_WITH_MASK)
    # merge mask for FG(1) and probable FG(3)
    mask = ((mask | 2) == 3).astype(np.uint8)
    return mask.tolist()


@api_view(["POST"])
@permission_classes((permissions.IsAuthenticated,))
def grab_cut_api(request):
    image = request.data.get("image")
    background_r = request.data.get("background_r")
    foreground_r = request.data.get("foreground_r")
    mask = grab_cut(image, background_r, foreground_r)
    result = {
        'mask': mask
    }
    return Response(result, status=HTTP_200_OK)


# scan config and cmd related
@api_view(["GET"])
@permission_classes((permissions.IsAuthenticated,))
def get_scan_config(request):
    with open(os.path.join(settings.SCAN_CONFIG_ROOT, 'config.json'), encoding="utf8") as f:
        config_file = json.load(f)
    with open(os.path.join(settings.SCAN_CONFIG_ROOT, 'name.json'), encoding="utf8") as f:
        name_file = json.load(f)
    with open(os.path.join(settings.SCAN_CONFIG_ROOT, 'description.json'), encoding="utf8") as f:
        description_file = json.load(f)
    result = {
        "config_file": config_file,
        "name_file": name_file,
        "description_file": description_file
    }
    return Response(result, status=HTTP_200_OK)


@api_view(["POST"])
@permission_classes((permissions.IsAuthenticated,))
def update_scan_config(request):
    config_file = request.data.get("config_file")
    with open(os.path.join(settings.SCAN_CONFIG_ROOT, 'config.json'), 'w', encoding="utf8") as outfile:
        json.dump(config_file, outfile, indent=4)
    return Response("ok", status=HTTP_200_OK)


@api_view(["POST"])
@permission_classes((permissions.IsAuthenticated,))
def scan_execute_cmd(request):
    cmd = request.data.get("cmd")
    if ';' not in cmd and (
            cmd.lower().startswith('motor') or cmd.lower().startswith('camera') or cmd.lower().startswith('ping')):
        # execute command
        try:
            ret = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, timeout=10)
        except subprocess.TimeoutExpired as e:
            return Response(
                {'flag': False, 'result': 'cmd:{} timeout! stdout:{} stderr:{}'.format(cmd, e.stdout, e.stderr)},
                status=HTTP_408_REQUEST_TIMEOUT)
        if ret.returncode == 0:
            # success
            flag = True
            result = ret.stdout
        else:
            # fail
            flag = False
            result = ret.stderr
        return Response({'flag': flag, 'result': result}, status=HTTP_200_OK)
    else:
        return Response({'flag': False, 'result': 'cmd:{} not valid!'.format(cmd)}, status=HTTP_403_FORBIDDEN)


# bbox related
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def generate_bbox(request, pk=None):
    scan = Scan.objects.get(id=pk)
    if scan.bbox_ready != 1:
        generate_bbox_scan(scan)
    return Response({'generated'}, status=HTTP_200_OK)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def add_bbox(request, pk=None):
    scan = Scan.objects.get(id=pk)
    array_key = request.data.get("array")
    bbox = request.data.get("bbox")
    position = request.data.get("position")
    if scan.bbox_ready == 2:
        return_bbox = add_bbox_scan(scan, array_key, bbox, position)
        return Response({'bbox': return_bbox}, status=HTTP_200_OK)
    else:
        return Response({'failed'}, status=HTTP_403_FORBIDDEN)


@api_view(['DELETE'])
@permission_classes((permissions.IsAuthenticated,))
def delete_bbox(request, pk=None):
    scan = Scan.objects.get(id=pk)
    array_key = request.data.get("array")
    position = request.data.get("position")
    if scan.bbox_ready == 2:
        delete_bbox_scan(scan, array_key, position)
        return Response({'deleted'}, status=HTTP_200_OK)
    else:
        return Response({'failed'}, status=HTTP_403_FORBIDDEN)


class PingView(APIView):
    """
    API ping
    """

    def get(self, request, format=None):
        content = {
            'status': f'hello {request.user}'
        }
        return Response(content)


class PhysicianViewSet(viewsets.ModelViewSet):
    """
    API users list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Physician.objects.all()
    serializer_class = PhysicianSerializer
    pagination_class = None

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as exc:
            return Response("user exists!", status=status.HTTP_409_CONFLICT)

    def retrieve(self, request, pk, *args, **kwargs):
        instance = Physician.objects.get(user=pk)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, pk, *args, **kwargs):
        instance = Physician.objects.get(user=pk)
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def destroy(self, request, pk, *args, **kwargs):
        instance = Physician.objects.get(user=pk)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# scan related
class UserDefinedFilter(django_filters.FilterSet):
    class Meta:
        model = UserDefined
        # filterset_fields can't be all, because of json related fields!
        fields = ['name']


class UserDefinedViewSet(viewsets.ModelViewSet):
    """
    API users list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = UserDefined.objects.all()
    serializer_class = UserDefinedSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filter_class = UserDefinedFilter
    ordering_fields = '__all__'
    ordering = ['created']


class ReportViewSet(viewsets.ModelViewSet):
    """
    API users list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    parser_classes = [JSONParser, MultiPartParser]
    pagination_class = None

    @action(detail=True, methods=['post'])
    def hospital_logo(self, request, pk=None, **kwargs):
        report = self.get_object()
        if report and report.id:
            f = request.parser_context['request'].data['file']
            media_folder = settings.SCAN_MEDIA_PATH
            # check media folder exists
            if not exists(media_folder):
                os.makedirs(media_folder, exist_ok=True)
            file_path = os.path.join(media_folder, f.name)
            if exists(file_path):
                os.remove(file_path)
            with open(file_path, "wb") as target:
                target.write(f.file.getbuffer())
            report.hospital_logo = f.name
            report.save(update_fields=['hospital_logo'])
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def get_report_config(self, request):
        result = {
            "config_file": get_report_config()
        }
        return Response(result, status=HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def update_report_config(self, request):
        config_file = request.data.get("config_file")
        report_config_file = os.path.join(settings.SCAN_SERVER_CONFIG_ROOT, 'scan_server_report_config.json')
        with open(report_config_file, 'w', encoding="utf8") as outfile:
            json.dump(config_file, outfile, indent=4)
        return Response("ok", status=HTTP_200_OK)

class MicroscopeViewSet(viewsets.ModelViewSet):
    """
    API users list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Microscope.objects.all()
    serializer_class = MicroscopeSerializer
    pagination_class = None


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'


class InListFilter(django_filters.Filter):
    """
    Expects a comma separated list
    filters values in list
    """

    def filter(self, qs, value):
        if value:
            return qs.filter(**{self.field_name + '__in': value.split(',')})
        return qs


class CharRangeFilter(django_filters.RangeFilter):
    class CharRangeField(fields.RangeField):
        widget = RangeWidget

        def __init__(self, *args, **kwargs):
            fields = (
                forms.CharField(),
                forms.CharField())
            super().__init__(fields, *args, **kwargs)

    field_class = CharRangeField


# LIS patient info to specimen entity
def register_patient_info(patient_info):
    if 'examine_id' in patient_info:
        # use examine_id as specimen_id
        specimen_id = patient_info['examine_id']
    else:
        specimen_id = patient_info['specimen_id']
    
    # create or update specimen entity
    try:
        specimen_entity = Specimen.objects.get_or_create(specimen_id=specimen_id)[0]
    except MultipleObjectsReturned as e:
        # multiple specimen entity with same specimen_id, get the most recent one
        specimen_entity = Specimen.objects.filter(specimen_id=specimen_id).order_by('-created')[0]
    for k, v in patient_info.items():
        setattr(specimen_entity, k, v)
    # set specimen_id as examine_id
    specimen_entity.examine_id = specimen_id
    specimen_entity.save()
    return specimen_entity


def check_query_LIS_patient_info(specimen_id):
    report_config = get_report_config()
    LIS_config = report_config['LIS']
    return_info = LIS_config['return_info']
    # message_key = return_info['message_key']
    # status_key = return_info['status_key']
    # success_condition = return_info['success_condition']
    if 'patient_info_api' in LIS_config:
        patient_info_api_config = LIS_config['patient_info_api']
        if patient_info_api_config['flag']:
            url = patient_info_api_config['url']
            if url:
                try:
                    res = requests.post(url, json={'examine_id': specimen_id})
                    if res.status_code < 300:
                        # just return full body, {'code': 0-成功，1-查无此人，2-错误，‘patient_info’: ***, 'message': ***}
                        return res.json()
                    else:
                        logger.error('request LIS patient info api error! {}'.format(res.content))
                except Exception as e:
                    logger.error('request LIS patient info api error!')
                    logger.error(traceback.format_exc())
    return None

class SpecimenFilter(django_filters.FilterSet):
    created_date = django_filters.DateFilter(field_name="created", lookup_expr='date')
    created_range = django_filters.DateFromToRangeFilter(field_name="created", lookup_expr='date')

    class Meta:
        model = Specimen
        # filterset_fields can't be all, because of json related fields!
        fields = ['name', 'specimen_id', 'created', 'created_date', 'created_range', 'reference_hospital']


class SpecimenViewSet(viewsets.ModelViewSet):
    """
    API users list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Specimen.objects.all()
    serializer_class = SpecimenSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filter_class = SpecimenFilter
    ordering_fields = '__all__'
    ordering = ['-created']
    
    @action(detail=False, methods=['get'])
    def LIS_patient_info(self, request):
        # get specimen_id
        specimen_id = request.query_params.get('specimen_id')
        
        patient_info = check_query_LIS_patient_info(specimen_id)
        if patient_info is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        # with LIS return
        if int(patient_info['code']) == 0:
            # get one, save or update it
            specimen_entity = register_patient_info(patient_info['patient_info'])
            serializer = self.get_serializer(specimen_entity)
            patient_info['patient_info'] = serializer.data

        # int the code key
        patient_info['code'] = int(patient_info['code'])
        return Response(patient_info, status=status.HTTP_200_OK)


def set_checkbox_value(report_data, checkbox_config, checkbox_diagnosisValue):
    for node_config in checkbox_config:
        # check if disabled
        if node_config['properties']['disabled']:
            continue
      
        # get checkbox_diagnosisValue node
        node_value = None
        for diagnosis_node in checkbox_diagnosisValue:
            if diagnosis_node['properties']['node_key'] == node_config['properties']['node_key']:
                node_value = diagnosis_node
        # check node exist
        if not node_value:
            continue
        
        # check if parent node or leaf node
        if_LIS_parent_node = False
        if_LIS_leaf_node = False
        if 'LIS_parent_node' in node_config['properties'] and node_config['properties']['LIS_parent_node']:
            if_LIS_parent_node = True
        if not node_config['children'] or len(node_config['children']) == 0:
            if_LIS_leaf_node = True
        LIS_key = node_config['properties']['LIS_key'] if node_config['properties']['LIS_key'] else node_config['properties']['node_key']
        if not if_LIS_parent_node and not if_LIS_leaf_node:
            # recurse to next level
            set_checkbox_value(report_data, node_config['children'], node_value['children'])
        elif if_LIS_leaf_node:
            # leaf node, just set LIS_value
            LIS_value = node_value['properties']['value']
            if LIS_value and LIS_value != 'unchecked':
                LIS_value = True
            else:
                LIS_value = False
            report_data[LIS_key] = LIS_value
        elif if_LIS_parent_node:
            # parent node
            # check children
            if not node_value['children'] or len(node_value['children']) == 0:
                report_data[LIS_key] = None
            # get true in child
            child_node_value = None
            for child in node_value['children']:
                child_value = child['properties']['value']
                if child_value and child_value != 'unchecked':
                    child_value = True
                else:
                    child_value = False
                if child_value:
                    child_node_value = child
            if child_node_value:
                # true in child
                # get child config info
                child_node_config = None
                for child in node_config['children']:
                    if child['properties']['node_key'] == child_node_value['properties']['node_key']:
                        child_node_config = child
                if not child_node_config:
                    # no config
                    report_data[LIS_key] = None
                LIS_value = child_node_config['properties']['LIS_value'] if child_node_config['properties']['LIS_value'] is not None else True
                report_data[LIS_key] = LIS_value
            else:
                # no ture in child
                LIS_value = child_node_config['properties']['LIS_parent_default_value']
                report_data[LIS_key] = LIS_value        
        

def set_conclusion_value(report_data, conclusion_config, conclusion_diagnosisValue):
    # check and set conclusion
    if conclusion_config['disabled']:
        return
    LIS_key = conclusion_config['LIS_key'] if conclusion_config['LIS_key'] else conclusion_config['node_key'] 
    report_data[LIS_key] = conclusion_diagnosisValue['value']
    
    # check and set suggesion
    if not conclusion_config['suggestion'] or len(conclusion_config['suggestion']) == 0:
        return
    if not conclusion_diagnosisValue['suggestion'] or len(conclusion_diagnosisValue['suggestion']) == 0:
        return
    for suggestion_config in conclusion_config['suggestion']:
        LIS_key = suggestion_config['LIS_key'] if suggestion_config['LIS_key'] else suggestion_config['node_key']
        suggestion_value = None
        for sv in conclusion_diagnosisValue['suggestion']:
            if sv['node_key'] == suggestion_config['node_key']:
                suggestion_value = sv
        if not suggestion_value:
            report_data[LIS_key] = None
        report_data[LIS_key] = suggestion_value['value']


class ScanFilter(django_filters.FilterSet):
    status = InListFilter(field_name='status')
    created_date = django_filters.DateFilter(field_name="created", lookup_expr='date')
    created_range = django_filters.DateFromToRangeFilter(field_name="created", lookup_expr='date')
    specimen_id_contains = django_filters.CharFilter(field_name='specimen_info__specimen_id', lookup_expr='icontains')
    specimen_id_startswith = django_filters.CharFilter(field_name='specimen_info__specimen_id',
                                                       lookup_expr='istartswith')
    specimen_range = CharRangeFilter(field_name='specimen_info__specimen_id', lookup_expr='iexact')
    micro_type_contains = django_filters.CharFilter(field_name='micro_type', lookup_expr='icontains')
    specimen_name_contains = django_filters.CharFilter(field_name='specimen_info__name', lookup_expr='icontains')

    class Meta:
        model = Scan
        # filterset_fields can't be all, because of json related fields!
        fields = ['specimen_info__name', 'specimen_info__specimen_id', 'specimen_id_contains', 'AIdiagnosis',
                  'status', 'scan_folder', 'created', 'AIgrade', 'specimen_qualified', 'micro_flag', 'disabled',
                  'created_date', 'occupied_by', 'owner__id', 'owner__username', 'created_range', 'reference_hospital',
                  'specimen_range', 'micro_type_contains', 'specimen_info__reference_department',
                  'specimen_info__reference_doctor', 'specimen_id_startswith', 'specimen_name_contains',
                  'backup_flag']


class ScanViewSet(viewsets.ModelViewSet):
    """
    API users list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Scan.objects.all()
    serializer_class = ScanSerializer
    parser_classes = [JSONParser, MultiPartParser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, RelatedOrderingFilter]
    filter_class = ScanFilter
    ordering_fields = '__all_related__'
    ordering = ['created']

    @action(detail=False, methods=['post'])
    def export_scan(self, request):
        # export scan to export folder
        data = request.data
        if data and data['scan']:
            for i in data['scan']:
                ins = Scan.objects.get(pk=i)
                export_scan(ins)
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return Response(status=HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def import_scan(self, request):
        # export scan to export folder
        data = request.data
        if data and data['scan_path']:
            import_scan(data['scan_path'])
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return Response(status=HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def backup_scan_to_path(self, request):
        # export scan to export folder
        data = request.data
        backup_path = data['backup_path']
        backup_scan_to_path(backup_path)
        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def submit_report(self, request, pk=None, **kwargs):
        scan = self.get_object()
        data = request.data
        folder = os.path.join(settings.SCAN_PATH, scan.scan_folder, 'report')
        if not exists(folder):
            os.makedirs(folder, exist_ok=True)
        # save report pics, 现在是写死的保存2个图片
        file_path_list = []
        if 'file_1' in data:
            file_1 = data['file_1']
            file_1_path = os.path.join(folder, 'file_1')
            if exists(file_1_path):
                os.remove(file_1_path)
            with open(file_1_path, "wb") as target:
                target.write(file_1.file.getbuffer())
            data.pop('file_1')
            file_path_list.append(file_1_path)

        if 'file_2' in data:
            file_2 = data['file_2']
            file_2_path = os.path.join(folder, 'file_2')
            if exists(file_2_path):
                os.remove(file_2_path)
            with open(file_2_path, "wb") as target:
                target.write(file_2.file.getbuffer())
            data.pop('file_2')
            file_path_list.append(file_2_path)

        # save everything to scan
        for k, v in data.items():
            if k == 'diagnosisValue' and type(v) == str:
                # string to json
                v = json.loads(v)
            setattr(scan, k, v)
        scan.save()
        
        # if status == authored, check if send report to LIS
        if 'status' in data and data['status'] == 'approved':
            report_data = {}
            # get report config
            report_config = get_report_config()
            LIS_config = report_config['LIS']
            # check LIS flag
            if not LIS_config['flag']:
                return Response(status=HTTP_202_ACCEPTED)
            logger.info("sending report to LIS...")
            # get all LIS contents
            # images config，现在是固定发送2个图片
            screenshot = report_config['screenshot']                
            num_files = len(file_path_list)
            files = {}
            for i in range(num_files):
                file_name = 'file_{}'.format(i + 1)
                # add to report data
                with open(file_path_list[i], "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read())
                    report_data[file_name] = encoded_string
                # add to file, 为了防止无法识别
                files[file_name] = ('{}.jpg'.format(file_name), open(file_path_list[i], 'rb'))
                    
            report_data['num_files'] = num_files
            
            # scan info
            scan_info = LIS_config['scan_info']
            for info in scan_info:
                node_key = info['node_key']
                LIS_key = info['LIS_key'] if info['LIS_key'] else node_key
                value = getattr(scan, node_key)
                # convert date type value
                if 'date' in type(value).__name__:
                    value = value.astimezone().strftime('%Y-%m-%dT%H:%M:%S')
                report_data[LIS_key] = value
            # specimen info
            specimen_info = LIS_config['specimen_info']
            for info in specimen_info:
                node_key = info['node_key']
                LIS_key = info['LIS_key'] if info['LIS_key'] else node_key
                value = getattr(scan.specimen_info, node_key)
                # convert date type value
                if 'date' in type(value).__name__:
                    value = value.astimezone().strftime('%Y-%m-%dT%H:%M:%S')
                report_data[LIS_key] = value
            # checkbox info
            checkbox_config = report_config['checkbox']
            checkbox_diagnosisValue = scan.diagnosisValue['checkbox']
            set_checkbox_value(report_data, checkbox_config, checkbox_diagnosisValue)
            # conclusion and suggestion
            conclusion_config = report_config['conclusion']
            conclusion_diagnosisValue = scan.diagnosisValue['conclusion']
            set_conclusion_value(report_data, conclusion_config, conclusion_diagnosisValue)
            
            # url rule
            url_rules = LIS_config['url_rule']
            url = None
            for url_rule in url_rules:
                match = re.search(url_rule['examine_id_rule'], scan.specimen_info.specimen_id)
                if match:
                    url = url_rule['url']
            if not url:
                return Response(data={'msg': 'no url matched! please check config！'},
                    status=HTTP_404_NOT_FOUND)                
            
            # send request
            return_info = LIS_config['return_info']
            message_key = return_info['message_key']
            status_key = return_info['status_key']
            success_condition = return_info['success_condition']
            
            # check value 
            # return Response(data={
            #         "url": url,
            #         "report_data": report_data,
            #         "return_info": return_info},
            #         status=HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                # prepare request
                # req = requests.Request('POST', url, files=files, data=report_data)
                # prepared = req.prepare()
                # logger.debug('request prepared:{}'.format(prepared.data))
                if 'content_type' in LIS_config and LIS_config['content_type'] == 'json':
                    # application/json post
                    res = requests.post(url, json=report_data)
                else:
                    # default form-data post
                    res = requests.post(url, files=files, data=report_data)
                if res.status_code < 300:
                    body = res.json()
                    if message_key and message_key in body:
                        message = body[message_key]
                    else:
                        message = '无message'
                    if status_key and status_key in body:
                        status = body[status_key]
                    else:
                        status = '无status'
                    if success_condition['key'] == 'status_code' or locals()[success_condition['key']] == success_condition['value']:
                        # success
                        return Response(data={'message': 'success! return msg:{}'.format(message),
                                            'status': status}, status=HTTP_202_ACCEPTED)
                    else:
                        # fail
                        return Response(data={'message': 'send request to LIS failed. return msg:{}'.format(message),
                                            'status': status},
                                        status=HTTP_400_BAD_REQUEST)
                else:
                    body = res.json()
                    logger.debug('LIS return body:{}'.format(body))
                    if type(body) == str:
                        # try parse json if str
                        body = json.loads(body)
                    if message_key and message_key in body:
                        message = body[message_key]
                    else:
                        message = '无message'
                    if status_key and status_key in body:
                        status = body[status_key]
                    else:
                        status = '无status'
                    return Response(data={'message': 'send request to LIS failed. return msg:{}'.format(message),
                                        'status': status},
                                    status=HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(data={'message': '发生LIS调用接口错误：{}'.format(traceback.format_exc())}, status=HTTP_400_BAD_REQUEST)

        return Response(status=HTTP_202_ACCEPTED)

    def list(self, request, *args, **kwargs):
        excl = request.query_params.get('excluding')
        if excl:
            # excluding fields
            excl_list = excl.split(',')
            queryset = self.filter_queryset(self.get_queryset().defer(*excl_list))

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True, remove_fields=excl_list)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True, remove_fields=excl_list)
            return Response(serializer.data)
        else:
            return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        excl = request.query_params.get('excluding')
        if excl:
            # excluding fields
            excl_list = excl.split(',')
            self.queryset = self.queryset.defer(*excl_list)
            instance = self.get_object()
            serializer = self.get_serializer(instance, remove_fields=excl_list)
            return Response(serializer.data)
        else:
            return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        detail = request.query_params.get('detail')
        # get specimen_id and update
        data = request.data
        
        # check specimen_info content
        specimen_info = None
        if 'specimen_info' in data:
            specimen_info = data['specimen_info'] 
        
        if specimen_info is not None and 'id' in specimen_info:
            # specimen_info with id
            pass
        else:
            # no id in specimen_info, find scan and specimen_info related
            specimen_id = None
            if 'specimen_id' in data:
                specimen_id = data['specimen_id']
            elif specimen_info is not None and 'specimen_id' in specimen_info:
                specimen_id = specimen_info['specimen_id']
            
            if specimen_id is None:
                # only update scan
                pass
            else:
                # get or create related specimen_info
                if specimen_id in ['not detected', 'empty']:
                    # not detected or empty, just create one, scan控制没有识别出二维码或者二维码为空时创建新的specimen
                    specimen_entity = Specimen.objects.create(specimen_id=specimen_id)
                else:
                    # check specimen entity first
                    if Specimen.objects.filter(specimen_id=specimen_id).exists():
                        specimen_entity = Specimen.objects.filter(specimen_id=specimen_id).order_by('-created')[0]
                    else:
                        # check if query LIS, or create empty entity
                        patient_info = check_query_LIS_patient_info(specimen_id)
                        if patient_info and int(patient_info['code']) == 0:
                            specimen_entity = register_patient_info(patient_info['patient_info'])
                        else:
                            # create empty specimen entity, if no LIS patient_info api available.
                            specimen_entity = Specimen.objects.get_or_create(specimen_id=specimen_id)[0]

                data['specimen_info'] = {'id': specimen_entity.id}
        
        r = super().update(request, *args, **kwargs)
        if detail and detail.lower() == 'true':
            return r
        else:
            return Response(status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, pk=None, **kwargs):
        id_list = [int(i) for i in pk.split(',')]
        instances = Scan.objects.filter(id__in=id_list)
        query_params = request.query_params
        for instance in instances:
            # check if reserved_flag is True
            if instance.reserved_flag:
                continue
            update_to_be_delete_scan(instance)
            # disable soft delete
            # if query_params and query_params['deleted'].lower() == 'true':
            #     hard_delete_scan(instance)
            # else, update_to_be_delete_scan:
            #     soft_delete_scan(instance)
        return Response(status=status.HTTP_202_ACCEPTED)


class PatientFilter(django_filters.FilterSet):
    created_date = django_filters.DateFilter(field_name="created", lookup_expr='date')

    class Meta:
        model = Patient
        # filterset_fields can't be all, because of json related fields!
        fields = ['name', 'specimen_id', 'created', 'created_date']


class PatientViewSet(viewsets.ModelViewSet):
    """
    API users list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filter_class = PatientFilter
    ordering_fields = '__all__'
    ordering = ['created']


class DoctorFilter(django_filters.FilterSet):
    created_date = django_filters.DateFilter(field_name="created", lookup_expr='date')

    class Meta:
        model = Doctor
        # filterset_fields can't be all, because of json related fields!
        fields = ['name', 'department', 'created_date']


class DoctorViewSet(viewsets.ModelViewSet):
    """
    API users list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filter_class = DoctorFilter
    ordering_fields = '__all__'
    ordering = ['created']


class DepartmentFilter(django_filters.FilterSet):
    created_date = django_filters.DateFilter(field_name="created", lookup_expr='date')

    class Meta:
        model = Department
        # filterset_fields can't be all, because of json related fields!
        fields = ['name', 'created_date']


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API users list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filter_class = DepartmentFilter
    ordering_fields = '__all__'
    ordering = ['created']


class ScheduledTaskViewSet(viewsets.ModelViewSet):
    """
    API scheduled task list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = ScheduledTask.objects.all()
    serializer_class = ScheduledTaskSerializer

    def update(self, request, *args, **kwargs):
        data = request.data
        task = self.get_object()
        update_run_at = False
        minute_of_hour = task.minute_of_hour
        hour_of_day = task.hour_of_day
        if 'minute_of_hour' in data.keys():
            minute_of_hour = data['minute_of_hour']
            update_run_at = True
        if 'hour_of_day' in data.keys():
            hour_of_day = data['hour_of_day']
            update_run_at = True
        if update_run_at:
            now = timezone.now()
            today = datetime.date.today()
            time_of_day = datetime.time(hour=hour_of_day, minute=minute_of_hour)
            run_at = datetime.datetime.combine(today, time_of_day)
            run_at = make_aware(run_at)
            if now < run_at:
                # set time today later
                data['run_at'] = run_at
            else:
                # set time tomorrow
                tomorrow = today + datetime.timedelta(days=1)
                run_at = datetime.datetime.combine(tomorrow, time_of_day)
                run_at = make_aware(run_at)
                data['run_at'] = run_at
        return super().update(request, *args, **kwargs)


# sp related
class SPMonitorViewSet(viewsets.ModelViewSet):
    """
    API scheduled task list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = SPMonitor.objects.all()
    serializer_class = SPMonitorSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        req = request.data
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        # send updates to websocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("monitor_{}".format(instance.id), {
            "type": "monitor_info",
            'bytes_data': JSONRenderer().render(serializer.validated_data)
        })

        return Response(serializer.data)


class SPMachineFilter(django_filters.FilterSet):
    created_date = django_filters.DateFilter(field_name="created", lookup_expr='date')
    created_range = django_filters.DateFromToRangeFilter(field_name="created", lookup_expr='date')

    class Meta:
        model = SPMachine
        # filterset_fields can't be all, because of json related fields!
        fields = ['name', 'hostname', 'created_range', 'created_date', 'ip', 'mac']


class SPMachineViewSet(viewsets.ModelViewSet):
    """
    API scheduled task list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = SPMachine.objects.all()
    serializer_class = SPMachineSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filter_class = SPMachineFilter
    ordering_fields = '__all__'
    ordering = ['created']

    def create(self, request, *args, **kwargs):
        data = request.data
        # check if dulplicate create
        name = data['name']
        try:
            sp_machine = SPMachine.objects.get(name=name)
            serializer = self.get_serializer(sp_machine)
            return Response(serializer.data)
        except SPMachine.DoesNotExist:
            return super().create(request, *args, **kwargs)


class SPSampleFilter(django_filters.FilterSet):
    process_status = InListFilter(field_name='process_status')
    finish_status = InListFilter(field_name='finish_status')
    created_date = django_filters.DateFilter(field_name="created", lookup_expr='date')
    created_range = django_filters.DateFromToRangeFilter(field_name="created", lookup_expr='date')
    launch_date = django_filters.DateFilter(field_name="last_launch_timestamp", lookup_expr='date')
    launch_range = django_filters.DateFromToRangeFilter(field_name="last_launch_timestamp", lookup_expr='date')

    class Meta:
        model = SPSample
        # filterset_fields can't be all, because of json related fields!
        fields = ['process_status', 'finish_status', 'created_range', 'created_date', 'sp_machine', 'barcode_scan',
                  'barcode_print', 'today_launch_count_id', 'today_processing_batch_id', 'launch_date', 'launch_range']


class SPSampleViewSet(viewsets.ModelViewSet):
    """
    API scheduled task list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = SPSample.objects.all()
    serializer_class = SPSampleSerializer
    parser_classes = [JSONParser, MultiPartParser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filter_class = SPSampleFilter
    ordering_fields = '__all__'
    ordering = ['created']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def files(self, request, pk=None, **kwargs):
        sample = self.get_object()
        if sample and sample.id:
            f = request.parser_context['request'].data['file']
            # check sample folder exists
            if sample.sample_folder is None:
                sample.sample_folder = uuid.uuid1().hex
                sample.save(update_fields=['sample_folder'])
            folder = os.path.join(settings.SP_FILE_PATH, sample.sample_folder)
            if not exists(folder):
                os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, f.name), "wb") as target:
                target.write(f.file.getbuffer())
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        # delete files after
        response = super(SPSampleViewSet, self).destroy(request, pk=None)
        folder = os.path.join(settings.SP_FILE_PATH, pk)
        rm_folder(folder)
        return response


class SPLogFilter(django_filters.FilterSet):
    created_date = django_filters.DateFilter(field_name="created", lookup_expr='date')
    created_range = django_filters.DateFromToRangeFilter(field_name="created", lookup_expr='date')

    class Meta:
        model = SPLog
        # filterset_fields can't be all, because of json related fields!
        fields = ['created_range', 'created_date', 'sp_machine']


class SPLogViewSet(viewsets.ModelViewSet):
    """
    API scheduled task list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = SPLog.objects.all()
    serializer_class = SPLogSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filter_class = SPLogFilter
    ordering_fields = '__all__'
    ordering = ['created']


class SPAlertFilter(django_filters.FilterSet):
    code = InListFilter(field_name='code')
    level = InListFilter(field_name='level')
    created_date = django_filters.DateFilter(field_name="created", lookup_expr='date')
    created_range = django_filters.DateFromToRangeFilter(field_name="created", lookup_expr='date')
    launch_date = django_filters.DateFilter(field_name="last_launch_timestamp", lookup_expr='date')
    launch_range = django_filters.DateFromToRangeFilter(field_name="last_launch_timestamp", lookup_expr='date')
    
    class Meta:
        model = SPAlert
        # filterset_fields can't be all, because of json related fields!
        fields = ['code', 'level', 'created_range', 'created_date', 'source', 'sp_machine', 'today_launch_count_id', 
                  'today_processing_batch_id', 'launch_date', 'launch_range']


class SPAlertViewSet(viewsets.ModelViewSet):
    """
    API scheduled task list
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = SPAlert.objects.all()
    serializer_class = SPAlertSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filter_class = SPAlertFilter
    ordering_fields = '__all__'
    ordering = ['created']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        if serializer.data['level'] in settings.SP_ALERT_LEVEL:
            # send alert to websocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "alert_{}".format(serializer.data['sp_machine']['id']),
                {
                    'type': 'alert_info',
                    'bytes_data': JSONRenderer().render(serializer.data)
                }
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# common
class ActionFilter(django_filters.FilterSet):
    class Meta:
        model = Action
        # filterset_fields can't be all, because of json related fields!
        fields = '__all__'


class ActionViewSet(viewsets.ModelViewSet):
    """
    API action list
    """
    permission_classes = [permissions.AllowAny]
    queryset = Action.objects.all()
    serializer_class = ActionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filter_class = ActionFilter
    ordering_fields = '__all__'
    ordering = ['created']


# LIS related
@csrf_exempt
@api_view(["POST"])
@permission_classes((AllowAny,))
def register_examine(request):
    try:
        # create specimen info from request
        body = request.data
        # register LIS patient info
        register_patient_info(body)
        return Response(status=HTTP_200_OK, data={'code': 0})
    except Exception as e:
        return Response(status=HTTP_200_OK, data={'code': 1, 
                                                  'message': '请求失败！请检查请求体内容。 body:{}'.format(body)})