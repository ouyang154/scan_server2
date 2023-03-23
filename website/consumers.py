import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from rest_framework.compat import INDENT_SEPARATORS
from rest_framework.renderers import JSONRenderer
from rest_framework.settings import api_settings
from rest_framework.utils import encoders

from website.models import SPMonitor
from website.serializers import SPMonitorSerializer


class EchoConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        self.send(text_data="hi")


class SPMonitorConsumer(WebsocketConsumer):
    encoder_class = encoders.JSONEncoder
    ensure_ascii = not api_settings.UNICODE_JSON
    compact = api_settings.COMPACT_JSON
    strict = api_settings.STRICT_JSON
    separators = INDENT_SEPARATORS
    indent = None

    def connect(self):
        self.monitor_id = int(self.scope['url_route']['kwargs']['monitor_id'])
        self.group_name = 'monitor_{}'.format(self.monitor_id)

        # Join
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data=None, bytes_data=None):
        # refresh monitor info, send back to caller only
        monitor = SPMonitor.objects.get(id=self.monitor_id)
        serializer = SPMonitorSerializer(monitor)
        ret = json.dumps(
            serializer.data, cls=self.encoder_class,
            indent=self.indent, ensure_ascii=self.ensure_ascii,
            allow_nan=not self.strict, separators=self.separators
        )
        self.send(text_data=ret)

    # Receive message from group
    def monitor_info(self, event):
        ret = event['bytes_data'].decode('utf-8')
        self.send(text_data=ret)


class SPAlertConsumer(WebsocketConsumer):

    def connect(self):
        self.machine_id = int(self.scope['url_route']['kwargs']['machine_id'])
        self.group_name = 'alert_{}'.format(self.machine_id)

        # Join
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, bytes_data=None, text_data=None):
        # receive alert info and send
        self.send(text_data="hi")

    # Receive message from group
    def alert_info(self, event):
        ret = event['bytes_data'].decode('utf-8')
        self.send(text_data=ret)
