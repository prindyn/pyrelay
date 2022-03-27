from machine import Pin, Signal


class Relay():
    pins = {1: 27, 2: 26, 3: 25, 4: 33, 5: 32, 6: 17, 7: 22, 8: 21}

    @classmethod
    def reset_states(self):
        for index, pin in self.pins.items():
            Signal(pin, Pin.IN).value(1)

    @classmethod
    def statuses(self, request):
        result = {}

        for index, pin in self.pins.items():
            result[index] = int(not Signal(pin, Pin.INOUT).value())
        return request.send_json({
            "status": 0,
            "data": result
        })

    @classmethod
    def setState(self, request):
        try:
            relay = request.params['relay']
            state = not request.params['state']
            pin = Signal(self.pins[relay], Pin.INOUT)
            try:
                pin(state)
            except KeyError:
                result = {
                    "status": -1,
                    "message": b"Relay state param missed"
                }
            result = {"status": 0, "data": {
                "relay": relay,
                "port": self.pins[relay],
                "state": int(not pin.value())
            }}
            return request.send_json(result)
        except KeyError:
            result = {
                "status": -1,
                "message": b"Relay number missed or not exist"
            }
            return request.send_json(result)
