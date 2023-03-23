from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'api/ws/echo/$', consumers.EchoConsumer),
    re_path(r'api/ws/sp/monitor/(?P<monitor_id>\w+)/$', consumers.SPMonitorConsumer),
    re_path(r'api/ws/sp/alert/(?P<machine_id>\w+)/$', consumers.SPAlertConsumer),
]
