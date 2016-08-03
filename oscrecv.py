#!/usr/bin/env python
"""
oscrecv.py

Run an OSCServer to control the lamp from touchOSC.
"""
import types
import platform
from OSC import OSCServer

# Local libraries
import lighthouse
import util

recv_port = 8000


class ServerLighthouse(object):

    def __init__(self, address=None, recvPort=recv_port):
        if address is None:
            address = util.get_ip()[0]  # Just use first detected address.
        self.address = address
        self.recv_port = recv_port
        self.timed_out = False

        # Setup a reciever for OSC.
        self.server = OSCServer((self.address, self.recv_port))
        self.server.timeout = False
        def handle_timeout(self):
            self.timed_out = True
        self.server.handle_timeout = types.MethodType(handle_timeout, self.server)

    def handle_timeout(self):
        self.timed_out = True
        # Startup light
        self.intitialize_light()

    def each_frame(self):
        # clear timed_out flag
        self.server.timed_out = False

        # handle all pending requests then return
        while not self.server.timed_out:
            self.server.handle_request()

    def handle_event(self, address, function, singleArg=True):
        def internal_function(path, tags, args, source):
            args = [int(arg) for arg in args]
            if singleArg:
                function(args[0])
            else:
                function(args)
        self.server.addMsgHandler(address, internal_function)

    def handle_touch(self, address, function):
        def internal_function(path, tags, args, source):
            arg = [int(arg) for arg in args]
            function(arg)

        address += '/z'
        self.server.addMsgHandler(address, internal_function)


class LighthouseMotion(ServerLighthouse):

    def __init__(self):
        super(LighthouseMotion, self).__init__()

        # Startup light
        self.intitialize_light()

    def intitialize_light(self):
        # Allow lamp to move at 25% speed.

        self.light = lighthouse.Lighthouse()
        self.light.set_speed(25)  # set speed to quarter AKA Rabtule (rabbit turtle)'

    def pan_light(self, address):
        self.handle_event(address, self.light.set_pan_position)
        return 'pan'

    def tilt_light(self, address):
        self.handle_event(address, self.light.set_tilt)
        return 'tilt'

    def set_speed(self, address):
        self.handle_event(address, self.light.set_speed)
        return 'speed'

    def light_on_off(self, address):
        self.handle_event(address, self.light.set_lamp)

    def set_brightness(self, address):
        self.handle_event(address, self.light.set_lamp)

    def set_strobe(self, address):
        self.handle_event(address, self.light.set_strobe)

    def printFunc(self, message):
        print(message)

    def printAthing(self, address):
        self.handle_event(address, self.printFunc, singleArg=False)


def controlLight(address):
    return '/controlLight/' + address


def lightStates(address):
    return '/lightStates' + address

if __name__ == "__main__":

    # Cribbed from https://github.com/ArdentHeavyIndustries/amcp-rpi/blob/master/server.py
    if platform.system() == "Darwin":
        service = None
    else:
        # Avahi announce so it's findable on the controller by name
        from avahi_announce import ZeroconfService
        service = ZeroconfService(
            name="BRLS TouchOSC Server", port=8000, stype="_osc._udp")
        service.publish()

    light = LighthouseMotion()
    light.pan_light('/staticLight/pan')
    light.tilt_light('/staticLight/tilt')
    light.set_speed('/staticLight/speed')
    light.light_on_off('/staticLight/lightControl')
    light.set_brightness('/staticLight/brightness')
    light.set_strobe('/staticLight/strobe')
    light.printAthing('/dynamicLight/xy1')
    while True:
        light.each_frame()
