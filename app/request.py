import ure
import json
from app.web import Web


class Request():
    path = ''
    action = ''
    params = {}
    conn = None
    black_list = ['/favicon.ico']

    @classmethod
    def process(self, request, conn):
        self.conn = conn
        self.header = self.parse_header(request)
        self.parse_url(self.header.get('url'))
        if self.path == '/api':
            self.handle_api_request()
        else:
            self.handle_request()

    @classmethod
    def send(self, data):
        return self.conn.send(data)

    @classmethod
    def send_json(self, data):
        data = {k: v for k, v in sorted(data.items())}
        return self.conn.send(json.dumps(data))

    @classmethod
    def handle_request(self):
        try:
            if self.path in self.black_list:
                return self.send_json({
                    "status": -1,
                    "message": "Forbiden access"
                })
            if self.path == '/':
                Web.welcome(self)
        except:
            return self.send_json({
                "status": -1,
                "message": "Unknown request"
            })

    @classmethod
    def handle_api_request(self):
        url = self.header.get('url').split('/')
        self.parse_url('/'+'/'.join(url[3:]))
        try:
            if not self.path or not self.action:
                raise Exception
            if self.path == '/relay':
                from app.relay import Relay
                action = getattr(Relay, self.action)
            action(self)
        except:
            return self.send_json({
                "status": -1,
                "message": "Unknown action"
            })

    @classmethod
    def parse_header(self, request):
        try:
            first_line = request[0]
            (verb, url, version) = first_line.split()
            result = {'verb': verb, 'url': url, 'version': version}
            for h in request:
                h = h.split(': ')
                if len(h) < 2:
                    continue
                field = h[0].strip()
                value = h[1].strip()
                result[field] = value
            return result
        except:
            return {}

    @classmethod
    def parse_url(self, url):
        try:
            params = {}
            path = ure.search("(.*?)(\?|$)", url)
            path = path.group(1).split('/')[1:]
            if len(path) > 1:
                self.action = path[1].strip()
            self.path = '/' + path[0]
            while True:
                vars = ure.search("(([a-z0-9]+)=([a-z0-8.]*))&?", url)
                if vars:
                    params[vars.group(2)] = vars.group(3)
                    url = url.replace(vars.group(0), '')
                else:
                    break
            self.params = params
        except:
            pass


class Requitto():
    path = ''
    action = ''
    params = {}
    mqtt = None
    black_list = []

    @classmethod
    def process(self, url, params, mqtt):
        self.mqtt = mqtt
        self.parse_url(url, params)
        self.handle_request()

    @classmethod
    def send(self, data):
        return self.mqtt.send(data)

    @classmethod
    def send_json(self, data):
        data = {k: v for k, v in sorted(data.items())}
        return self.mqtt.client.publish(
            self.mqtt.topic_pub,
            json.dumps(data)
        )

    @classmethod
    def data(self):
        return self.header

    @classmethod
    def auth_check(self):
        pass

    @classmethod
    def handle_request(self):
        try:
            if not self.path or not self.action:
                raise Exception
            action = self.action
            if self.path == '/relay':
                from app.relay import Relay
                action = getattr(Relay, self.action)
            action(self)
        except:
            return self.send_json({
                "status": -1,
                "message": "Unknown api action"
            })

    @classmethod
    def parse_url(self, url, params):
        try:
            path = url.split('/')[3:]
            if len(path) > 1:
                self.action = path[1].strip()
            self.path = '/' + path[0]
            self.params = json.loads(params)
        except:
            pass
