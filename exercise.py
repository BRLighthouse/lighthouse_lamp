import time

import lighthouse

l = lighthouse.Lighthouse()
try:
    l.set_lamp(0)
    l.set_speed(100)
    rot_dir = True
    while True:
        rot_dir = not rot_dir
        print 'tilt 0'
        l.set_lamp(1)
        l.set_rotation(rot_dir, speed=20)
        l.set_tilt(-30)
        time.sleep(2)
        l.set_lamp(1)
        l.set_tilt(0)
        time.sleep(2)
        l.set_tilt(45)
        l.set_lamp(100)
        print 'tilt 45'
        time.sleep(2)
        l.set_lamp(50)
        l.set_tilt(90)
        print 'tilt 90'
        time.sleep(2)
finally:
    print 'shutting down.'
    l.set_lamp(0)
    time.sleep(1)
    l.dmx.disconnect()
