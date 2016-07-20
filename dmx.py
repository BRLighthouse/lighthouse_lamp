import os
from enttec_usb_dmx_pro import EnttecUsbDmxPro
from util import get_default_port

def colorize_output(*s):
    RED = '\033[93m'
    return '\033[95m'+RED+' '.join([str(x) for x in s])+'\033[0m'

if os.path.exists(get_default_port()):
    Dmx = EnttecUsbDmxPro.EnttecUsbDmxPro
else:
    class Dmx(object):
        def __init__(self):
            print colorize_output('Enttec port device', get_default_port(), 'not found. Starting fake DMX...')
            
        def setPort(self, port, baud=None):
            print colorize_output('setting port...', port)

        def connect(self):
            print colorize_output('connecting...')

        def setChannel(self, channel, value, autoRender=True):
            print colorize_output('setting channel', channel, value, autoRender)

        def render(self, render_till=None):
            print colorize_output('rendering...', render_till if render_till is not None else '')

        def blackOut(self):
            print colorize_output('Blacking out...')

        def disconnect(self):
            print colorize_output('disconecting...')
