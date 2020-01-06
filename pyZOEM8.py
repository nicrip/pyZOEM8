#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import smbus
import time
import math
import datetime
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
        # curses.nocbreak()
        # curses.echo()
        # curses.endwin()
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
        self.position_status = 'invalid'
        self.mode = 'invalid'
        self.latitude = -1
        self.longitude = -1
        self.quality = 'invalid'
        self.num_satellites = -1
        self.horizontal_dilution = -1
        self.altitude = -1
        self.geoid_undulation = -1
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
            console.clear()
            loop_start = time.time()
            loop_time = loop_start - prev_loop_start
            prev_loop_start = loop_start

            self.read()

            console.addstr(0,0,'Reading ZOE-M8Q GNSS Sensor')
            console.addstr(1,0,'')
            console.addstr(2,0,'UTC:')
            console.addstr(3,0,'    Seconds: {:10.3f} s'.format(self.utc))
            console.addstr(4,0,'    Date: {:06d}'.format(self.utc_date))
            console.addstr(5,0,'    Time: {:6.3f} s'.format(self.utc_time))
            console.addstr(6,0,'')
            console.addstr(7,0,'Position:')
            console.addstr(8,0,'    Status: ' + self.position_status)
            console.addstr(9,0,'    Longitude: {:6.5f} deg'.format(self.longitude))
            console.addstr(10,0,'    Latitude: {:6.5f} deg'.format(self.latitude))
            console.addstr(11,0,'    Altitude: {:6.5f} m'.format(self.altitude))
            console.addstr(12,0,'')
            console.addstr(13,0,'Mode: ' + self.mode)
            console.addstr(14,0,'Quality: ' + self.quality)
            console.addstr(15,0,'Number of Satellites: {:3d}'.format(self.num_satellites))
            console.addstr(16,0,'Horizontal Dilution of Precision: {:2.1f}'.format(self.horizontal_dilution))
            console.addstr(17,0,'')
            console.addstr(18,0,'Speed-over-Ground: {:3.2f} knots'.format(self.speed_over_ground))
            console.addstr(19,0,'Course-over-Ground: {:3.2f} deg'.format(self.course_over_ground))
            console.addstr(20,0,'')
            console.addstr(21,0,'Loop Cycle Time: {:4.2f} ms'.format(loop_time*1e3))
            console.addstr(22,0,'')
            console.addstr(23,0,'Press `q` to quit.')
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
                if gps_components[2] != '':
                    latitude = float(gps_components[2])
                    latitude_d = int(latitude/100.0)
                    latitude_m = latitude - latitude_d*100.0
                    latitude = latitude_d + latitude_m/60.0
                    latitude_sign = gps_components[3]
                    if latitude_sign == 'S':
                        latitude = -latitude
                    self.latitude = latitude
                if gps_components[4] != '':
                    longitude = float(gps_components[4])
                    longitude_d = int(longitude/100.0)
                    longitude_m = longitude - longitude_d*100.0
                    longitude = longitude_d + longitude_m/60.0
                    longitude_sign = gps_components[5]
                    if longitude_sign == 'W':
                        longitude = -longitude
                    self.longitude = longitude
                if gps_components[6] != '':
                    quality = int(gps_components[6])
                    if quality == 0:
                        quality = 'invalid'
                    elif quality == 1:
                        quality = 'single point'
                    elif quality == 2:
                        quality = 'pseudorange differential'
                    elif quality == 4:
                        quality = 'RTK fixed'
                    elif quality == 5:
                        quality = 'RTK floating'
                    elif quality == 6:
                        quality = 'dead reckoning'
                    elif quality == 7:
                        quality = 'manual input'
                    elif quality == 8:
                        quality = 'simulator'
                    elif quality == 9:
                        quality = 'WAAS'
                    else:
                        quality = 'invalid'
                    self.quality = quality
                if gps_components[7] != '':
                    self.num_satellites = int(gps_components[7])
                if gps_components[8] != '':
                    self.horizontal_dilution = float(gps_components[8])
                if gps_components[9] != '':
                    self.altitude = float(gps_components[9])
                if gps_components[11] != '':
                    self.geoid_undulation = float(gps_components[11])

        if (gps_msg == "$GNRMC"):
            check_val = 0
            for ch in gps_str[1:]:
                check_val ^= ord(ch)
            if (check_val == int(check_sum, 16)):
                if gps_components[1] != '' and gps_components[9] != '':
                    utc_time = float(gps_components[1])
                    utc_date = gps_components[9]
                    hours = int(math.floor(utc_time/1.0e4))
                    mins = int(math.floor((utc_time - hours*1.0e4)/1.0e2))
                    secs = int(math.floor(utc_time - (hours*1.0e4+mins*1.0e2)))
                    usecs = int(math.floor((utc_time - (hours*1.0e4+mins*1.0e2+secs))*1e6))
                    year = int(utc_date[-2:]) + 2000
                    month = int(utc_date[-4:-2])
                    day = int(utc_date[0:-4])
                    dt = datetime.datetime(year, month, day, hours, mins, secs, usecs)
                    timestamp = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
                    self.utc_time = utc_time
                    self.utc_date = int(utc_date)
                    self.utc = timestamp
                status = gps_components[2]
                if status == 'A':
                    status = 'valid'
                else:
                    status = 'invalid'
                self.position_status = status
                if gps_components[7] != '':
                    self.speed_over_ground = float(gps_components[7])
                if gps_components[8] != '':
                    self.course_over_ground = float(gps_components[8])
                mode = gps_components[12]
                if mode == 'N':
                    mode = 'invalid'
                elif mode == 'A':
                    mode = 'autonomous'
                elif mode == 'D':
                    mode = 'differential'
                elif mode == 'E':
                    mode = 'dead-reckoning'
                else:
                    mode = 'invalid'
                self.mode = mode

zoe_m8q = ZOEM8(2)
zoe_m8q.run()
