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
        self.utc_time = -1
        self.utc_date = -1
        self.utc = -1
        self.latitude = -1
        self.longitude = -1
        self.quality = -1
        self.num_satellites = -1
        self.horizontal_dilation = -1
        self.altitude = -1
        self.geoid_height = -1
        self.speed_over_ground = -1
        self.course_over_ground = -1

        # initialize i2c bus
        try:
            self.ZOEM8 = initBus(bus_num)
        except:
            print('No i2c device detected on bus{:2d}!'.format(bus_num))
            exit(1)
        print('i2c bus initialized on bus{:2d}.'.format(bus_num))

    def run(self):
        prev_loop_start = time.time()
        console = curses.initscr()
        curses.noecho()
        curses.cbreak()
        console.keypad(True)
        console.nodelay(True)
        input = None
        while True:
            loop_start = time.time()
            loop_time = loop_start - prev_loop_start
            prev_loop_start = loop_start

            self.read()

            console.addstr(0,0,'Reading ZOE-M8Q GNSS Sensor')
            console.addstr(1,0,'')
            console.addstr(2,0,'UTC:')
            console.addstr(3,0,'    Seconds: {:10d} s'.format(self.utc))
            console.addstr(4,0,'    Date: {:6d}'.format(self.utc_date))
            console.addstr(5,0,'    Time: {:6.3f}'.format(self.utc_time))
            console.addstr(6,0,'')
            console.addstr(7,0,'Position:')
            console.addstr(8,0,'    Longitude: {:6.3f} deg'.format(self.longitude))
            console.addstr(9,0,'    Latitude: {:6.3f} deg'.format(self.latitude))
            console.addstr(10,0,'    Altitude: {:6.3f} deg'.format(self.altitude))
            console.addstr(11,0,'')
            console.addstr(12,0,'Quality: {:2d}'.format(self.quality))
            console.addstr(13,0,'Number of Satellites: {:3d}'.format(self.num_satellites))
            console.addstr(14,0,'Horizontal Dilation of Precision: {:2.1f}'.format(self.horizontal_dilation))
            console.addstr(15,0,'')
            console.addstr(16,0,'Speed-over-Ground: {:3.2f}'.format(self.speed_over_ground))
            console.addstr(17,0,'Course-over-Ground: {:3.2f}'.format(self.course_over_ground))
            console.addstr(18,0,'')
            console.addstr(19,0,'Loop Cycle Time: {:4.2f} ms'.format(loop_time*1e3))
            console.addstr(20,0,'')
            console.addstr(21,0,'Press `q` to quit.')
            console.refresh()

            time.sleep(READ_INTERVAL)

            try:
                input = console.getkey()
            except:
                pass

            if input == 'q':
                curses.nocbreak()
                console.nodelay(False)
                console.keypad(False)
                curses.echo()
                curses.endwin()
                print('Quitting ZOEM8 program.')
                sys.exit(0)

    def read(self):
        c = None
        response = []
        try:
            while True: # Newline, or bad char.
                c = self.ZOEM8.read_byte(ZOEM8Q_ADDR)
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
        except Exception as e:
            print(e)

    def parseResponse(self, gps_line):
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
                pass
                # print(gps_components)
                # print(gps_chars)

        if (gps_msg == "$GNRMC"):
            check_val = 0
            for ch in gps_str[1:]:
                check_val ^= ord(ch)
            if (check_val == int(check_sum, 16)):
                pass
                # print(gps_components)
                # print(gps_chars)

zoe_m8q = ZOEM8(2)
zoe_m8q.run()
