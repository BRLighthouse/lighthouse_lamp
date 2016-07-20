#!/usr/bin/env python 

# stdlib
import platform
import types

# dependent libraries
from OSC import OSCServer

# Local libraries
import lighthouse

recv_port = 7000

class ServerLighthouse(object):

    def __init__(self, address='192.168.1.145', recv_port=recv_port):

        self.address = address
        self.recv_port = recv_port

        self.timed_out = False

        # Setup a reciever for OSC.
        self.server = OSCServer((self.address, self.recv_port))
        self.server.timeout = 0
        self.server.handle_timeout = types.MethodType(ServerLighthouse.handle_timeout, self)

        # Startup light
        self.intitialize_light()

    def handle_timeout(self):
        self.timed_out = True

    def each_frame(self):
        # clear timed_out flag
        self.server.timed_out = False

        # handle all pending requests then return
        while not self.server.timed_out:
            self.server.handle_request()

    def handle_event(self, address, function):
        def internal_function(path, tags, args, source):
            arg = int(args[0])
            function(arg)
        self.server.addMsgHandler(address, internal_function)

class LighthouseMotion(ServerLighthouse):

    def __init__(self):
        super(LighthouseMotion, self).__init__()

    def intitialize_light(self):
        # Allow lamp to move at 25% speed.

        self.light = lighthouse.Lighthouse()
        self.light.set_speed(25)  # set speed to quarter AKA Rabtule (rabbit turtle)

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
    light.pan_light('/1/pan')
    light.tilt_light('/1/tilt')
    light.set_speed('/1/speed')
    light.light_on_off('/1/lightcontrol')
    light.set_brightness('/1/brightness')
    light.set_strobe('/1/strobe')
    while True:
        light.each_frame()
