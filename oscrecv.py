#!/usr/bin/env python
"""
oscrecv.py

Run an OSCServer to control the lamp from touchOSC.
"""
# Stdlib
import platform
import sys
import threading
import time

# Libraries
from OSC import OSCServer

# Local libraries
from lighthouse import Lighthouse
import util

default_recv_port = 8000


def avahi_publisher(server):
    # Cribbed from https://github.com/ArdentHeavyIndustries/amcp-rpi/blob/master/server.py
    if platform.system() == "Darwin":
        service = None
    else:
        # Avahi announce so it's findable on the controller by name
        from avahi_announce import ZeroconfService
        service = ZeroconfService(
            name="BRLS TouchOSC Server", port=server.server_address[1], stype="_osc._udp")
        service.publish()

class ServerLighthouse(OSCServer):
    """
    OSCServer for lighthouse.

    Turns OSC messages into reality functions.
    """

    def __init__(self, address=None, recv_port=default_recv_port):
        if address is None:
            address = '0.0.0.0'
        OSCServer.__init__(self, (address, recv_port))
        print('Starting OSC Server at %s on port %s' % (address, recv_port))

    def handle_event(self, address, function, touchFunction=None):
        """
        Whenever an OSCMessage is passed from the Client to the Server, do a thing with it.

        The internal function is used by the MsgHandler to take all arguments from the source,
        parse them into integers and pass them off to the desired function. The appropriate function
        for a touch event can also be passed in as well.
        """
        def internal_function(path, tags, args, source):
            args = [int(arg) for arg in args]
            function(*args)

        self.addMsgHandler(address, internal_function)
        self.handle_touch(address, touchFunction)

    def handle_touch(self, address, function):
        """
        Handle a touch event from TouchOSC.

        If none is passed in as the function make a blank handler, this was mainly for my sainty.
        """
        if function:
            def internal_function(path, tags, args, source):
                arg = [int(arg) for arg in args]
                function(arg)
        else:
            def internal_function(*args):
                pass

        address += '/z'
        self.addMsgHandler(address, internal_function)

class PingHandler(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.ping_dict = {}
        self.die = False
        self.sleep = 1

    def run(self):
        while not self.die:
            self.check_pings()
            time.sleep(self.sleep)

    def check_pings(self):
        gone_time = 61
        now = time.time()
        for address, v in self.ping_dict.items():
            delta = now - v
            if delta > gone_time:
                print "ping - Haven't seen", address, "for", delta, "seconds, removing."
                del self.ping_dict[address]

    def add_ping(self, address):
        self.ping_dict[address] = time.time()

class OSCPingHandler(object):
    def __init__(self):
        self.addMsgHandler('/ping/', self.ping_handler)

        self.pings = PingHandler()
        self.pings.start()

    def ping_handler(self, path, tags, args, message_source):
        """
            message_source looks like ('192.168.0.24', 47139)
            The port changes if the touchOSC app is relaunched so just use ip
        """
        address, port = message_source
        self.pings.add_ping(address)

    def close(self):
        self.pings.die = True
        self.pings.join()

class LighthouseOSCCallbacks(Lighthouse, ServerLighthouse, OSCPingHandler):
    def __init__(self, light_func_dict=None):
        ServerLighthouse.__init__(self)
        Lighthouse.__init__(self)
        OSCPingHandler.__init__(self)

        self.set_functions(light_func_dict)

    def set_functions(self, funcDict):
        # Pass a dictionary of OSC addresses and function names as callback functions to the OSCServer.
        for address, functionName in funcDict.iteritems():
            self.handle_event(address, getattr(self, functionName))

    def close(self):
        ServerLighthouse.close(self)
        OSCPingHandler.close(self)


if __name__ == "__main__":

    lightFunctions = {
        '/staticLight/pan': 'set_pan_position',
        '/staticLight/tilt': 'set_tilt',
        '/staticLight/speed': 'set_speed',
        '/staticLight/lightControl': 'set_lamp',
        '/staticLight/brightness': 'set_lamp',
        '/staticLight/strobe': 'set_strobe',
    }

    light = LighthouseOSCCallbacks(lightFunctions)
    avahi_publisher(light)

    while True:
        try:
            light.serve_forever()
        except (KeyboardInterrupt):
            light.shutdown_light()
        finally:
            light.close()
            sys.exit()
