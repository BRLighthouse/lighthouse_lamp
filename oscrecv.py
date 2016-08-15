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
import OSC
from OSC import OSCServer

# Local libraries
from lighthouse import Lighthouse
import util

IDLE_TIME_BEFORE_AUTOMATIC = 60 * 3
TIME_TO_CONSIDER_CLIENT_GONE = 61

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

class ServerLighthouse(OSC.ThreadingOSCServer):
    """
    OSCServer for lighthouse.

    Turns OSC messages into reality functions.
    """

    def __init__(self, address=None, recv_port=default_recv_port):
        if address is None:
            address = '0.0.0.0'
        OSCServer.__init__(self, (address, recv_port))
        print('Starting OSC Server at %s on port %s' % (address, recv_port))

    def am_idle(self):
        print 'Running idle...'
        self.set_speed(0)
        self.set_lamp(95)
        self.set_strobe(0)
        self.set_tilt(5)
        time.sleep(.5)
        self.set_rotation(True, speed=50)

    def handle_event(self, address, function, touchFunction=None):
        """
        Whenever an OSCMessage is passed from the Client to the Server, do a thing with it.

        The internal function is used by the MsgHandler to take all arguments from the source,
        parse them into integers and pass them off to the desired function. The appropriate function
        for a touch event can also be passed in as well.
        """
        def internal_function(path, tags, args, source):
            args = [int(arg) for arg in args]
            if source[0] == self.enabled:
                function(*args)
            else:
                print 'Ignoring command from', source[0], 'because', self.enabled, 'has control.'

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

class ClientPingHandler(object):
    """
        Listen for /ping/ messages and update last seen timestamps
    """
    def __init__(self):
        self.ping_dict = {}
        self.die = False
        self.sleep = 1
        self.addMsgHandler('/ping/', self.osc_ping_handler)
        self.thread = threading.Thread(target=self.worker)
        self.thread.start()

        class InterceptingRequestHandler(OSC.OSCRequestHandler):
            def handle(local_self):
                self.add_ping(local_self.client_address[0])
                return OSC.OSCRequestHandler.handle(local_self)
        self.RequestHandlerClass = InterceptingRequestHandler

    def worker(self):
        while not self.die:
            self.check_pings()
            time.sleep(self.sleep)

    def check_pings(self):
        gone_time = TIME_TO_CONSIDER_CLIENT_GONE
        now = time.time()
        for address, v in self.ping_dict.items():
            delta = now - v
            if delta > gone_time:
                print "ping - Haven't seen", address, "for", delta, "seconds, removing."
                del self.ping_dict[address]

    def osc_ping_handler(self, path, tags, args, message_source):
        """
            message_source looks like ('192.168.0.24', 47139)
            The port changes if the touchOSC app is relaunched so just use ip
        """
        address, port = message_source
        self.add_ping(address)
        self.send_status(address)

    def add_ping(self, address):
        self.ping_dict[address] = time.time()

    def close(self):
        self.die = True
        self.thread.join()

class IdleChecker(object):
    """
        Send a message to the server every X seconds.
        Check when the last request from a client was sent.
        If it was more than Y seconds, run idle command.
    """
    def __init__(self):
        self.die = False
        self.sleep = 1
        self.idle = False
        self.idle_enabled = True
        self.last = time.time()
        self.addMsgHandler('/admin/idle_enable', self.idle_toggle)
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        # Wait for IDLE_TIME_BEFORE_AUTOMATIC seconds after startup before
        # running idle pattern.
        time.sleep(IDLE_TIME_BEFORE_AUTOMATIC)
        while not self.die:
            self.update_clients()
            self.idle_check()
            time.sleep(self.sleep)

    def idle_check(self):
        # check when last req from client was sent
        now = time.time()
        client = None
        for client, timestamp in self.ping_dict.iteritems():
            if (now - timestamp) <= IDLE_TIME_BEFORE_AUTOMATIC:
                self.idle = False
                break
        else:
            # fires if break not run, so only when idle
            self.enabled = None # system is idle, no one has control
            if not self.idle:
                self.idle = True
                if self.idle_enabled:
                # idle animation is disabled via touchosc admin page
                    self.am_idle()
            return

        # break was hit - system still being used.
        print 'System still being used by', self.ping_dict.keys()
        pass

    def idle_toggle(self, path, data_types, raw_data, sender_port_tuple):
        data = int(raw_data[0])
        self.idle_enabled = data
        self.send_status(sender_port_tuple[0])

    def close(self):
        self.die = True
        self.thread.join()

class SendServerStatus(object):
    def __init__(self):
        self.client = OSC.OSCClient()

    def send_status(self, client_address):
        statuses = [
            ('/admin/idle_enable', int(self.idle_enabled)),
            ('/staticLight/lightControl', int(self.enabled == client_address)),
            ]
        for path, variable in statuses:
            self.send_message(client_address, path, variable)

    def send_message(self, client_address, path, variable):
        msg = OSC.OSCMessage(path)
        msg.append(variable, typehint='f')
        port = 8000 if client_address != '127.0.0.1' else 4000
        try:
            self.client.sendto(msg, (client_address, port))
        except OSC.OSCClientError:
            pass

    def update_clients(self):
        for client in self.ping_dict.iterkeys():
            self.send_status(client)

class LighthouseOSCCallbacks(Lighthouse, ServerLighthouse, ClientPingHandler, IdleChecker, SendServerStatus):
    def __init__(self, light_func_dict=None):
        ServerLighthouse.__init__(self)
        Lighthouse.__init__(self)
        ClientPingHandler.__init__(self)
        IdleChecker.__init__(self)
        SendServerStatus.__init__(self)

        self.set_functions(light_func_dict)
        self.addMsgHandler('default', self.print_msg)
        self.addMsgHandler('/staticLight/lightControl', self.request_control)

        self.enabled = None

    def print_msg(self, *args):
        print 'Unknown message: ', args

    def set_functions(self, funcDict):
        # Pass a dictionary of OSC addresses and function names as callback functions to the OSCServer.
        for address, functionName in funcDict.iteritems():
            self.handle_event(address, getattr(self, functionName))

    def close(self):
        ServerLighthouse.close(self)
        ClientPingHandler.close(self)
        IdleChecker.close(self)

    def request_control(self, path, data_types, raw_data, sender_port_tuple):
        sender = sender_port_tuple[0]
        if sender_port_tuple[0] == '127.0.0.1':
            return_port = 4000
        else:
            return_port = 8000

        data = int(raw_data[0])

        msg = OSC.OSCMessage(path)
        if data:
            print 'IP requesting control:', sender,
            if self.enabled:
                if sender == self.enabled:
                    # Already in control, but might have been issue on client side.
                    print 'already in control.'
                    msg.append(1, typehint='f')
                else:
                    # sender is not already in control. 2 cases: old controller still in control
                    if self.enabled in self.ping_dict:
                        print 'saw ping from previous controller recently.'
                        msg.append(0, typehint='f')
                    else:
                        print "haven't seen previous controller recently, transferring control."
                        msg.append(1, typehint='f')
                        self.enabled = sender
            else: # ! self.enabled
                print 'access granted.'
                msg.append(1, typehint='f')
                self.enabled = sender
        else: # data == 0
            print 'IP releasing control:', sender,
            if self.enabled == sender:
                print sender, 'released control'
                self.enabled = None
            else:
                print sender, "wasn't actually in control."
            msg.append(0, typehint='f')

        client = OSC.OSCClient()
        client.connect((sender, return_port))
        client.send(msg)
        client.close()

if __name__ == "__main__":

    lightFunctions = {
        '/staticLight/pan': 'set_pan_position',
        '/staticLight/tilt': 'set_tilt',
        '/staticLight/speed': 'set_speed',
        '/staticLight/lightControl': 'set_lamp',
        '/staticLight/brightness': 'set_lamp',
        #'/staticLight/strobe': 'blah',
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
