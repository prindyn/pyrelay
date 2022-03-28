import network
import machine
import _thread
import utime as time
import usocket as socket
import ubinascii as binascii
from app.request import Request
from app.request import Requitto
from lib.umqtt.simple import MQTTClient


class ThreadedServer(object):
    client = None

    def __init__(self, host, port, thread_id=''):
        self.host = host
        self.port = port
        self.id = thread_id if thread_id else binascii.hexlify(
            '%s:%s' % (host, port)).decode('utf-8')

    def sock(self):
        self.type = 'sock'
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client.bind((self.host, self.port))
        self.client.listen(5)
        return self

    def mqtt(self, client_id='', topic_sub='', topic_pub=''):
        self.type = 'mqtt'
        self.client_id = client_id if client_id else binascii.hexlify(
            machine.unique_id())
        self.topic_sub = topic_sub.encode() if topic_sub else b'/api/%s/#' % (self.client_id)
        self.topic_pub = topic_pub.encode() if topic_pub else b'/relay/%s' % (self.client_id)
        self.client = MQTTClient(self.client_id, self.host, self.port)
        return self

    def listen(self):
        _thread.allowsuspend(True)
        if self.type == 'sock':
            _thread.start_new_thread(
                self.id, self.listenSockClient, [self.client])
        if self.type == 'mqtt':
            # _thread.start_new_thread(
            # self.id, self.listenMqttClient, [self.client])
            self.listenMqttClient(self.client)

    def manage_ntf(self):
        ntf = _thread.getnotification()
        if ntf == -1:
            return
        elif ntf == 0:
            _thread.lock()
        elif ntf == 1:
            _thread.unlock()
        elif ntf == 7:
            print({"nth_id": _thread.getSelfName()})

    def listenSockClient(self, client):
        while True:
            client, address = self.client.accept()
            print('Client connected from', address)
            try:
                conn_file = client.makefile('rwb', 0)
                request = []
                while True:
                    header = conn_file.readline()
                    if not header or header == b'\r\n':
                        break
                    request.append(header.decode('utf-8'))
                Request.process(request, client)
            except:
                return False
            client.close()

    def listenMqttClient(self, client):
        def sub_cb(topic, msg):
            msg = msg.decode('utf-8')
            topic = topic.decode('utf-8')
            print('Received %s from topic %s' % (msg, topic))
            Requitto.process(topic, msg, self)

        def restart_and_reconnect():
            print('Failed to connect to MQTT broker. Reconnecting...')
            time.sleep(10)
            machine.reset()

        def subscribe(client):
            while True:
                try:
                    client.check_msg()
                except OSError as e:
                    restart_and_reconnect()

        client.set_callback(sub_cb)
        try:
            client.connect()
            client.subscribe(self.topic_sub)
        except OSError as e:
            self.restart_and_reconnect()
        print('Connected to %s MQTT broker, subscribed to %s topic' %
              (self.host, self.topic_sub))
        while True:
            try:
                client.check_msg()
            except OSError as e:
                restart_and_reconnect()


class Network(object):
    client = None
    essid = 'Relay-ESP32'
    ipaddr = '192.168.0.1'

    def __init__(self, password='', username='', mode='sta'):
        self.mode = mode
        self.username = username
        self.password = password

    def station(self):
        self.client = network.WLAN(network.STA_IF)
        self.client.active(True)
        return self

    def apoint(self, name='', ipaddr=''):
        essid = name if name else self.essid
        ipaddr = ipaddr if ipaddr else self.ipaddr
        self.client = network.WLAN(network.AP_IF)
        self.client.active(True)
        self.client.config(essid=essid, password=self.password)
        self.client.ifconfig(
            (ipaddr, '255.255.255.0', '192.168.0.1', '8.8.8.8'))
        return self

    def connected(self):
        if self.mode == 'ap':
            status = self.client.active()
        elif self.mode == 'sta':
            status = self.client.isconnected()
            if not status:
                self.client.connect(self.username, self.password)
        else:
            status = False
        return status

    def connect(self):
        tmo = 30
        print('Connecting to network...')
        try:
            while not self.connected():
                time.sleep(1)
                tmo -= 1
                if tmo == 0:
                    print('Network connection failed')
                    raise OSError
            print('Network connected', self.client.ifconfig())
            return self.client.ifconfig()
        except:
            return None

    def close(self):
        if self.client and self.connected():
            self.client.disconnect()
            self.client.activate(False)
        print('Network disconnected')
