from __future__ import division
import platform

from netifaces import interfaces, ifaddresses, AF_INET

def get_default_port():
    if platform.system() == 'Linux':
        return '/dev/ttyUSB0'
    elif platform.system() == 'Darwin':
        return '/dev/tty.usbserial-ENSML0W9'

def percent_to_dmx(int_percent):
    return int(int_percent/100 * 255)

def degrees_to_dmx(degrees, min_range=0, max_range=360):
    return int(degrees/(max_range-min_range) * 255)

def brightness_percent_to_dmx(int_percent):
    return 255 - percent_to_dmx(int_percent)

def tilt_to_dmx(int_tilt):
    """
    Horizontal is 0
    Vertical is 90
    below horizontal is < 0
    past vertical (light can go past 90 deg) is simply 90+
    """
    return int((int_tilt + 30) * (256/240))

def filter_out_ipv6_and_local_addresses(addresses):
    for x in addresses:
        if ':' in x:
            continue
        if x.startswith('172.'):
            continue
        if x.startswith('127.'):
            continue
        yield x

def get_ip():
    d_all_addresses = {}
    for interface_name in interfaces():
        addr = ifaddresses(interface_name)
        for family in addr.itervalues():
            for address in family:
                address['addr']
                d_all_addresses[address['addr']] = 1
    return list(filter_out_ipv6_and_local_addresses(d_all_addresses.keys()))
