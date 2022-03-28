import gc
from app.relay import Relay
from app.networking import Network, ThreadedServer


gc.collect()
Relay.reset_states()


# connection = Network(mode='ap').apoint().connect()
# if connection:
    # ThreadedServer(connection[0], 80).sock().listen()
connection = Network('06011993', '_prindyn').station().connect()
if connection:
    # ThreadedServer(connection[0], 80, 'web_socket').sock().listen()
    ThreadedServer('159.223.218.14', 1883, 'mqtt_server').mqtt().listen()
