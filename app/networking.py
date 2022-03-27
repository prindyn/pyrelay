import utime
import network
import usocket
import machine
import ubinascii
from app.request import Request
from app.request import Requitto
from lib.umqtt.simple import MQTTClient


class Network():
    wlan = None
    s_port = 80
    s_host = '0.0.0.0'
    username = '_prindyn'
    password = '06011993'

    def init(self) -> None:
        pass

    @classmethod
    def do_connect(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        if not self.wlan.isconnected():
            print('Connecting to network...')
            self.wlan.connect(self.username, self.password)
            while not self.wlan.isconnected():
                pass
            print('Network connected', self.wlan.ifconfig())
            return True

    @classmethod
    def do_close(self):
        if self.wlan and self.wlan.isconnected():
            self.wlan.disconnect()
            self.wlan.activate(False)
        print('Network disconnected!')

    @classmethod
    def socket_open(self):
        addr = usocket.getaddrinfo(self.s_host, self.s_port)[0][-1]
        s = usocket.socket()
        s.bind(addr)
        s.listen(1)
        print('Network listening on', addr)
        while True:
            request = []
            conn, addr = s.accept()
            print('client connected from', addr)
            conn_file = conn.makefile('rwb', 0)
            while True:
                header = conn_file.readline()
                if not header or header == b'\r\n':
                    break
                request.append(header.decode('utf-8'))
            Request.process(request, conn)
            conn.close()


class mqtt():
    client = None
    port = 1883
    server = '159.223.218.14'
    client_id = ubinascii.hexlify(machine.unique_id())
    topic_sub = b'/api/%s/#' % (client_id)
    topic_pub = b'/relay/%s' % (client_id)

    @classmethod
    def connect_and_subscribe(self):

        def sub_cb(topic, msg):
            msg = msg.decode('utf-8')
            topic = topic.decode('utf-8')
            print('ESP received %s from topic %s' % (msg, topic))
            Requitto.process(topic, msg, self)

        self.client = MQTTClient(self.client_id, self.server)
        self.client.set_callback(sub_cb)
        try:
            self.client.connect()
            self.client.subscribe(self.topic_sub)
        except OSError as e:
            self.restart_and_reconnect()

        print('Connected to %s MQTT broker, subscribed to %s topic' %
              (self.server, self.topic_sub))
        while True:
            try:
                self.client.check_msg()
            except OSError as e:
                self.restart_and_reconnect()

    @classmethod
    def restart_and_reconnect(self):
        print('Failed to connect to MQTT broker. Reconnecting...')
        utime.sleep(10)
        machine.reset()
