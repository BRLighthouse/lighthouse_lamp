import time

from util import (
    brightness_percent_to_dmx,
    degrees_to_dmx,
    get_default_port,
    percent_to_dmx,
    tilt_to_dmx,
)

from dmx import Dmx

CHANNEL_MASTER_CONTROL = 4
MASTER_LAMP_OFF = 100
MASTER_LAMP_ON = 255

CHANNEL_BRIGHTNESS = 6
# simple 0-255 scale

CHANNEL_PAN_LOCATION = 8

CHANNEL_PAN_MOVMENT = 12
PAN_GOTO_POS = 0
PAN_CW = 128
PAN_CCW = 250

CHANNEL_SPEED = 15
# Speed must be < 50% to safely change direction

CHANNEL_TILT = 10
TILT_LOW = 0
TILT_VERTICAL = 128
TILT_LOW_CONTROLBOX_SIDE = 255
TILT_LOW_DEGREES = -120
TILT_VERTICAL_DEGREES = 0

CHANNEL_STROBE = 7
STROBE_MIN = 25

PAN_DEAD_ZONE_LOCATIONS = [0, 60, 120, 180, 240, 300, 360]
# 0 only goes from 0->deadzonesize so we include 360 to cover the half of the deadzone side
PAN_DEAD_ZONE_SIZE = 10
PAN_DEAD_ZONES = [(max(0,x-PAN_DEAD_ZONE_SIZE), min(360, x+PAN_DEAD_ZONE_SIZE)) for x in PAN_DEAD_ZONE_LOCATIONS]

TILT_LIMIT_LOW = -5
TILT_LIMIT_HIGH = 70

def reposition_from_pan_deadzone(position_degrees):
    for lower_bound, upper_bound in PAN_DEAD_ZONES:
        if position_degrees < lower_bound:
            break
        if lower_bound <= position_degrees <= upper_bound:
            if (position_degrees - lower_bound) < (upper_bound - position_degrees):
                return max(lower_bound - 1, PAN_DEAD_ZONES[0][1]+1)
            else:
                return upper_bound + 1
    if position_degrees > PAN_DEAD_ZONES[-1][1]:
        return True, PAN_DEAD_ZONES[-1][0]-1
    return position_degrees

def reposition_from_tilt_deadzone(tilt_degrees):
    tilt_degrees = max(TILT_LIMIT_LOW, tilt_degrees)
    tilt_degrees = min(TILT_LIMIT_HIGH, tilt_degrees)
    return tilt_degrees

class Lighthouse(object):

    def __init__(self):
        self.brightness = 0

        self.dmx = Dmx() #EnttecUsbDmxPro.EnttecUsbDmxPro()
        self.port = get_default_port()
        self.dmx.setPort(self.port, baud=250000)
        self.dmx.connect()
        # print 'EntTec serial number:', self.dmx.getWidgetSerialNumber()
        # self.dmx.setDebug('SerialBuffer', True)
        self.dmx.setChannel(CHANNEL_MASTER_CONTROL, MASTER_LAMP_OFF, autoRender=False)
        self.dmx.setChannel(CHANNEL_PAN_LOCATION, degrees_to_dmx(180), autoRender=False)  # pan location
        self.dmx.setChannel(CHANNEL_TILT, TILT_VERTICAL, autoRender=False)  # tilt
        self.set_speed(25)
        self.dmx.render()

    def set_lamp(self, int_brightness):
        """
        Brightness is a percentage, 0-100%

        """
        self.brightness = int_brightness
        if self.brightness == 0:
            self.dmx.setChannel(CHANNEL_MASTER_CONTROL, MASTER_LAMP_OFF, autoRender=False)
            self.dmx.render()
            return
        self.dmx.setChannel(CHANNEL_MASTER_CONTROL, MASTER_LAMP_ON, autoRender=False)
        self.dmx.setChannel(CHANNEL_BRIGHTNESS, brightness_percent_to_dmx(self.brightness), autoRender=False)
        self.dmx.render()

    def set_pan_position(self, position_degrees):
        """
            Moves lamp to a specific position
            TODO - Add in don't-burn-down-lighthouse safeguard
        """
        position_degrees = reposition_from_pan_deadzone(position_degrees)
        self.dmx.setChannel(CHANNEL_PAN_LOCATION, degrees_to_dmx(position_degrees), autoRender=False)
        self.dmx.render()

    def set_rotation(self, clockwise, speed=100):
        """
            Set rotation and speed
            TODO - assert speed < 50% if already moving
        """
        self.dmx.setChannel(CHANNEL_SPEED, percent_to_dmx(0), autoRender=False)
        self.dmx.render()
        time.sleep(1)
        if clockwise:
            self.dmx.setChannel(CHANNEL_PAN_MOVMENT, PAN_CW, autoRender=False)
        else:
            self.dmx.setChannel(CHANNEL_PAN_MOVMENT, PAN_CCW, autoRender=False)
        self.dmx.setChannel(CHANNEL_SPEED, percent_to_dmx(speed), autoRender=False)
        self.dmx.render()

    def set_tilt(self, tilt_degrees):
        """
            Set the lamp's tilt, in degrees.

            0 is horizontal, 90 is vertical, 90+ is rotation in the other direction.
            The lowest it can go is -30 degrees.
        """
        tilt_degrees = reposition_from_tilt_deadzone(tilt_degrees)
        self.dmx.setChannel(CHANNEL_TILT, tilt_to_dmx(tilt_degrees), autoRender=False)
        self.dmx.render()

    def set_speed(self, speed_percent):
        """
            Set the speed in percent of dmx, range untested on actual lamp
        """
        self.dmx.setChannel(CHANNEL_SPEED, percent_to_dmx(speed_percent), autoRender=False)
        self.dmx.render()

    def set_strobe(self, strobe_percent):
        """
            Set the strobe percent of dmx, untested on actual lamp
        """
        self.dmx.setChannel(CHANNEL_STROBE, percent_to_dmx(strobe_percent), autoRender=False)
        self.dmx.render()

    def set_idle(self, ignored):
        self.set_speed(0)
        self.set_lamp(95)
        self.set_strobe(0)
        self.set_tilt(5)
        time.sleep(.5)
        self.set_rotation(True, speed=50)

    def shutdown_light(self):
        """
            It is important to stop the light, turn off the lamp and disconnect.
        """
        self.set_rotation(True, speed=0)
        self.set_lamp(0)
        time.sleep(2)
        self.dmx.disconnect()
