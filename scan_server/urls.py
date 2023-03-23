"""scan_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from website import views
from website.views import login, generate_bbox, add_bbox, delete_bbox, grab_cut_api, get_scan_config, scan_execute_cmd, \
    update_scan_config, register_examine

prefix = 'api'

router = routers.DefaultRouter()
router.register(r'users', views.PhysicianViewSet)
router.register(r'user_defined', views.UserDefinedViewSet)
router.register(r'micros', views.MicroscopeViewSet)
router.register(r'reports', views.ReportViewSet)
router.register(r'specimen', views.SpecimenViewSet)
router.register(r'scans', views.ScanViewSet)
router.register(r'patients', views.PatientViewSet)
router.register(r'doctors', views.DoctorViewSet)
router.register(r'departments', views.DepartmentViewSet)
router.register(r'tasks', views.ScheduledTaskViewSet)
router.register(r'sp/monitor', views.SPMonitorViewSet)
router.register(r'sp/machine', views.SPMachineViewSet)
router.register(r'sp/sample', views.SPSampleViewSet)
router.register(r'sp/log', views.SPLogViewSet)
router.register(r'sp/alert', views.SPAlertViewSet)
router.register(r'action', views.ActionViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('{}/ping/'.format(prefix), views.PingView.as_view()),
    path('{}/'.format(prefix), include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

urlpatterns += [
    url(r'{}/api-token-auth/'.format(prefix), login),
    url(r'{}/examine/register/'.format(prefix), register_examine),
    url(r'{}/grab_cut/'.format(prefix), grab_cut_api),
    url(r'{}/get_scan_config/'.format(prefix), get_scan_config),
    url(r'{}/update_scan_config/'.format(prefix), update_scan_config),
    url(r'{}/scan_execute_cmd/'.format(prefix), scan_execute_cmd),
    url(prefix+'/bbox/(?P<pk>.+)/generate/', generate_bbox),
    url(prefix+'/bbox/(?P<pk>.+)/add/', add_bbox),
    url(prefix+'/bbox/(?P<pk>.+)/delete/', delete_bbox)
]
