from app.relay import Relay
from app.networking import Network
from app.networking import mqtt

Relay.reset_states()

if Network.do_connect():
    mqtt.connect_and_subscribe()
