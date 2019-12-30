#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import smbus
import time
import math
import signal
import sys
import curses

# Sensor-specific definitions
# ZOE-M8Q
ZOEM8Q_ADDR             =0x42

READ_INTERVAL           =0.1

# initialize i2c bus
def initBus(bus_num):
    return smbus.SMBus(bus_num)

# write a byte to an open i2c bus
def writeByteToBus(bus, address, offset, data_byte):
    bus.write_byte_data(address, offset, data_byte)

# read 'count' bytes from an open i2c bus
def readBytesFromBus(bus, address, offset, count):
    bus.write_byte(address, offset)
    return [bus.read_byte(address) for k in range(count)]

def signal_handler(sig, frame):
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        print('Ctrl+C force quit.')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

class ZOEM8(object):
    def __init__(self, bus_num):
        self.bus_num = bus_num
        self.read_interval = READ_INTERVAL
        self.utc_time = None
        self.utc_date = None
        self.utc = None
        self.latitude = None
        self.longitude = None
        self.quality = None
        self.num_satellites = None
        self.horizontal_dilation = None
        self.altitude = None
        self.geoid_height = None
        self.speed_over_ground = None
        self.course_over_ground = None

        # initialize i2c bus
        try:
            self.ZOEM8 = initBus(bus_num)
        except:
            print('No i2c device detected on bus{:2d}!'.format(bus_num))
            exit(1)
        print('i2c bus initialized on bus{:2d}.'.format(bus_num))

    def run(self):
        pass

    def read(self):
        c = None
        response = []
        try:
            while True: # Newline, or bad char.
                c = self.ZOEMQ.read_byte(ZOEM8Q_ADDR)
                if c == 255:
                    return False
                elif c == 10:
                    break
                else:
                    response.append(c)
            self.parseResponse(response)
        except IOError:
            print('i2c device on bus{:2d} disconnected!'.format(bus_num))
            exit(1)
        except Exception, e:
            print(e)

    def parseResponse(self):
        gps_chars = ''.join(chr(c) for c in gps_line)
        if "*" not in gps_chars:
            return False

        gps_str, check_sum = gps_chars.split('*')
        gps_components = gps_str.split(',')
        gps_msg = gps_components[0]
        if (gps_msg == "$GNGGA"):
            check_val = 0
            for ch in gps_str[1:]:
                check_val ^= ord(ch)
            if (check_val == int(check_sum, 16)):
                # for i, k in enumerate(
                #     ['strType', 'fixTime',
                #     'lat', 'latDir', 'lon', 'lonDir',
                #     'fixQual', 'numSat', 'horDil',
                #     'alt', 'altUnit', 'galt', 'galtUnit',
                #     'DPGS_updt', 'DPGS_ID']):
                #     GPSDAT[k] = gpsComponents[i]
                print(gps_chars)

        if (gps_msg == "$GNRMC"):
            check_val = 0
            for ch in gps_str[1:]:
                check_val ^= ord(ch)
            if (check_val == int(check_sum, 16)):
                # for i, k in enumerate(
                #     ['strType', 'fixTime',
                #     'lat', 'latDir', 'lon', 'lonDir',
                #     'fixQual', 'numSat', 'horDil',
                #     'alt', 'altUnit', 'galt', 'galtUnit',
                #     'DPGS_updt', 'DPGS_ID']):
                #     GPSDAT[k] = gpsComponents[i]
                print(gps_chars)
