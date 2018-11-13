#!/usr/bin/env python3
"""
Polyglot v2 node server for MeteoBridge weather data.
Copyright (c) 2018 Robert Paauwe
"""
import polyinterface
import sys
import time
import datetime
import urllib3
import json
import socket
import math
import threading
import struct
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
import write_profile
import uom

LOGGER = polyinterface.LOGGER

class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'MeteoBridge'
        self.address = 'mbweather'
        self.primary = self.address
        self.port = 5557
        self.ip = ""
        self.units = ""
        self.temperature_list = {}
        self.humidity_list = {}
        self.pressure_list = {}
        self.wind_list = {}
        self.rain_list = {}
        self.light_list = {}
        self.lightning_list = {}
        self.myConfig = {}  # custom parameters

        self.poly.onConfig(self.process_config)

    def process_config(self, config):
        if 'customParams' in config:
            if config['customParams'] != self.myConfig:
                # Configuration has changed, we need to handle it
                LOGGER.info('New configuration, updating configuration')
                self.set_configuration(config)
                self.setup_nodedefs(self.units)
                self.discover()
                self.myConfig = config['customParams']

                # Remove all existing notices
                self.removeNoticesAll()

                # Add notices about missing configuration
                if self.ip == "":
                    self.addNotice("IP address of the MeteoBridge device is required.")
                if self.port == "":
                    self.addNotice("Port for the MeteoBridge device is required (default is 5557).")

    def start(self):
        LOGGER.info('Starting MeteoBridge Node Server')
        self.check_params()
        self.discover()
        LOGGER.info('MeteoBridge Node Server Started.')

    def shortPoll(self):
        pass

    def longPoll(self):
        # open socket and read data
        if self.ip == "" or self.port == "":
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mb_address = (self.ip, self.port)
            sock.connect(mb_address)
            header = "Content-type: text/xml; charset=UTF-8\n\n"
            sock.sendall(header.encode())
            xmldata = sock.recv(2048)

            LOGGER.debug(xmldata)
            # Parse the XML data
            try:
                tree = ET.XML(xmldata.decode())

                LOGGER.debug('tag = ' + tree.tag)
                for child in tree.getchildren():
                    LOGGER.debug('   child = ' + child.tag)
                    if child.tag == 'UV':
                        self.nodes['light'].setDriver(
                           uom.LITE_DRVS['uv'], float(child.get('index')))
                        LOGGER.debug('    UV index = ' + child.get('index'))
                    elif child.tag == 'SOL':
                        LOGGER.debug('    Solar   = ' + child.get('rad'))
                        self.nodes['light'].setDriver(
                            uom.LITE_DRVS['solar_radiation'],
                            float(child.get('rad')))
                    elif child.tag == 'RAIN':
                        if child.get('id') == 'rain0':
                            LOGGER.debug('    Rate    = ' + child.get('rate'))
                            LOGGER.debug('    Delta   = ' + child.get('delta'))
                            LOGGER.debug('    Total   = ' + child.get('total'))
                            self.nodes['rain'].setDriver(
                                uom.RAIN_DRVS['rate'], float(child.get('rate')))
                            self.nodes['rain'].setDriver(
                                uom.RAIN_DRVS['total'], float(child.get('total')))
                    elif child.tag == 'TH':
                        if child.get('id') == 'th0':
                            self.nodes['temperature'].setDriver(
                                uom.TEMP_DRVS['dewpoint'],
                                float(child.get('dew')))
                            self.nodes['temperature'].setDriver(
                                uom.TEMP_DRVS['main'], float(child.get('temp')))
                            self.nodes['humidity'].setDriver(
                                uom.HUMD_DRVS['main'], float(child.get('hum')))
                            LOGGER.debug('    Dewpoin = ' + child.get('dew'))
                            LOGGER.debug('    Humidit = ' + child.get('hum'))
                            LOGGER.debug('    Temp    = ' + child.get('temp'))
                    elif child.tag == 'THB':
                        if child.get('id') == 'thb0':
                            self.nodes['pressure'].setDriver(
                                uom.PRES_DRVS['station'], float(child.get('press')))
                            self.nodes['pressure'].setDriver(
                                uom.PRES_DRVS['sealevel'],
                                float(child.get('seapress')))
                            LOGGER.debug('    Dewpoin = ' + child.get('dew'))
                            LOGGER.debug('    Humidit = ' + child.get('hum'))
                            LOGGER.debug('    Temp    = ' + child.get('temp'))
                            LOGGER.debug('    Sea     = ' + child.get('seapress'))
                            LOGGER.debug('    pressur = ' + child.get('press'))
                    elif child.tag == 'WIND':
                        if child.get('id') == 'wind0':
                            self.nodes['temperature'].setDriver(
                                uom.TEMP_DRVS['windchill'],
                                float(child.get('chill')))
                            self.nodes['wind'].setDriver(
                                uom.WIND_DRVS['windspeed'], float(child.get('wind')))
                            self.nodes['wind'].setDriver(
                                uom.WIND_DRVS['gustspeed'], float(child.get('gust')))
                            self.nodes['wind'].setDriver(
                                uom.WIND_DRVS['winddir'], float(child.get('dir')))
                            LOGGER.debug('    chill   = ' + child.get('chill'))
                            LOGGER.debug('    wind    = ' + child.get('wind'))
                            LOGGER.debug('    gust    = ' + child.get('gust'))
                            LOGGER.debug('    direct  = ' + child.get('dir'))

            except:
                LOGGER.error("Failure while parsing MeteoBridge data.")
        except:
            LOGGER.error("Failure trying to connect to MeteoBridge device.")
        finally:
            sock.close()

    def query(self):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        """
        Add nodes for basic sensor type data
                - Temperature (temp, dewpoint, heat index, wind chill, feels)
                - Humidity
                - Pressure (abs, sealevel, trend)
                - Wind (speed, gust, direction, gust direction, etc.)
                - Precipitation (rate, hourly, daily, weekly, monthly, yearly)
                - Light (UV, solar radiation, lux)
                - Lightning (strikes, distance)

        The nodes need to have thier drivers configured based on the user
        supplied configuration. To that end, we should probably create the
        node, update the driver list, set the units and then add the node.
        """
        LOGGER.info("Creating nodes.")
        node = TemperatureNode(self, self.address, 'temperature', 'Temperatures')
        node.SetUnits(self.units);
        for d in self.temperature_list:
            node.drivers.append(
                    {
                        'driver': uom.TEMP_DRVS[d],
                        'value': 0,
                        'uom': uom.UOM[self.temperature_list[d]]
                        })
        self.addNode(node)

        node = HumidityNode(self, self.address, 'humidity', 'Humidity')
        node.SetUnits(self.units);
        for d in self.humidity_list:
            node.drivers.append(
                    {
                        'driver': uom.HUMD_DRVS[d],
                        'value': 0,
                        'uom': uom.UOM[self.humidity_list[d]]
                        })
        self.addNode(node)

        node = PressureNode(self, self.address, 'pressure', 'Barometric Pressure')
        node.SetUnits(self.units);
        for d in self.pressure_list:
            node.drivers.append(
                    {
                        'driver': uom.PRES_DRVS[d],
                        'value': 0,
                        'uom': uom.UOM[self.pressure_list[d]]
                        })
        self.addNode(node)

        node = WindNode(self, self.address, 'wind', 'Wind')
        node.SetUnits(self.units);
        for d in self.wind_list:
            node.drivers.append(
                    {
                        'driver': uom.WIND_DRVS[d],
                        'value': 0,
                        'uom': uom.UOM[self.wind_list[d]]
                        })
        self.addNode(node)

        node = PrecipitationNode(self, self.address, 'rain', 'Precipitation')
        node.SetUnits(self.units);
        for d in self.rain_list:
            node.drivers.append(
                    {
                        'driver': uom.RAIN_DRVS[d],
                        'value': 0,
                        'uom': uom.UOM[self.rain_list[d]]
                        })
        self.addNode(node)

        node = LightNode(self, self.address, 'light', 'Illumination')
        node.SetUnits(self.units);
        for d in self.light_list:
            node.drivers.append(
                    {
                        'driver': uom.LITE_DRVS[d],
                        'value': 0,
                        'uom': uom.UOM[self.light_list[d]]
                        })
        self.addNode(node)

    def delete(self):
        self.stopping = True
        LOGGER.info('Removing MeteoBridge node server.')

    def stop(self):
        self.stopping = True
        LOGGER.debug('Stopping MeteoBridge node server.')

    def check_params(self):
        self.set_configuration(self.polyConfig)
        self.setup_nodedefs(self.units)

        # Make sure they are in the params  -- does this cause a 
        # configuration event?
        LOGGER.info("Adding configuation")
        self.addCustomParam({
                    'UDPPort': self.port,
                    'IPAddress': self.ip,
                    'Units': self.units,
                    })

        self.myConfig = self.polyConfig['customParams']

        # Remove all existing notices
        LOGGER.info("remove all notices")
        self.removeNoticesAll()

        # Add a notice?
        if self.ip == "":
            self.addNotice("IP address of the MeteoBridge device is required.")
        if self.port == "":
            self.addNotice("Port for the MeteoBridge device is required (default is 5557).")

    def set_configuration(self, config):
        default_port = 5557
        default_ip = ""
        default_elevation = 0

        LOGGER.info("Check for existing configuration value")

        if 'Port' in config['customParams']:
            self.port = int(config['customParams']['UDPPort'])
        else:
            self.udp_port = default_port

        if 'IPAddress' in config['customParams']:
            self.ip = config['customParams']['IPAddress']
        else:
            self.ip = default_ip

        if 'Units' in config['customParams']:
            self.units = config['customParams']['Units']
        else:
            self.units = 'metric'

        return self.units

    def setup_nodedefs(self, units):

        # Configure the units for each node driver
        self.temperature_list['main'] = 'TEMP_F' if units == 'us' else 'TEMP_C'
        self.temperature_list['dewpoint'] = 'TEMP_F' if units == 'us' else 'TEMP_C'
        self.temperature_list['windchill'] = 'TEMP_F' if units == 'us' else 'TEMP_C'
        self.humidity_list['main'] = 'I_HUMIDITY'
        self.pressure_list['station'] = 'I_INHG' if units == 'us' else 'I_MB'
        self.pressure_list['sealevel'] = 'I_INHG' if units == 'us' else 'I_MB'
        self.wind_list['windspeed'] = 'I_MPS' if units == 'metric' else 'I_MPH'
        self.wind_list['gustspeed'] = 'I_MPS' if units == 'metric' else 'I_MPH'
        self.wind_list['winddir'] = 'I_DEGREE'
        self.rain_list['rate'] = 'I_MMHR' if units == 'metric' else 'I_INHR'
        self.rain_list['total'] = 'I_MM' if units == 'metric' else 'I_INCH'
        self.light_list['uv'] = 'I_UV'
        self.light_list['solar_radiation'] = 'I_RADIATION'

        # Build the node definition
        LOGGER.info('Creating node definition profile based on config.')
        write_profile.write_profile(LOGGER, self.temperature_list,
                self.humidity_list, self.pressure_list, self.wind_list,
                self.rain_list, self.light_list, self.lightning_list)

        # push updated profile to ISY
        try:
            self.poly.installprofile()
        except:
            LOGGER.error('Failed up push profile to ISY')

    def remove_notices_all(self,command):
        LOGGER.info('remove_notices_all:')
        # Remove all existing notices
        self.removeNoticesAll()

    def update_profile(self,command):
        st = self.poly.installprofile()
        return st

    def SetUnits(self, u):
        self.units = u


    id = 'MeteoBridge'
    name = 'MeteoBridgePoly'
    address = 'mbweather'
    stopping = False
    hint = 0xffffff
    units = 'metric'
    commands = {
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile,
        'REMOVE_NOTICES_ALL': remove_notices_all
    }
    # Hub status information here: battery and rssi values.
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2},
            {'driver': 'GV0', 'value': 0, 'uom': 72}, 
            ]


class TemperatureNode(polyinterface.Node):
    id = 'temperature'
    hint = 0xffffff
    units = 'metric'
    drivers = [ ]

    def SetUnits(self, u):
        self.units = u

    def Dewpoint(self, t, h):
        b = (17.625 * t) / (243.04 + t)
        rh = h / 100.0
        c = math.log(rh)
        dewpt = (243.04 * (c + b)) / (17.625 - c - b)
        return round(dewpt, 1)

    def ApparentTemp(self, t, ws, h):
        wv = h / 100.0 * 6.105 * math.exp(17.27 * t / (237.7 + t))
        at =  t + (0.33 * wv) - (0.70 * ws) - 4.0
        return round(at, 1)

    def Windchill(self, t, ws):
        # really need temp in F and speed in MPH
        tf = (t * 1.8) + 32
        mph = ws / 0.44704

        wc = 35.74 + (0.6215 * tf) - (35.75 * math.pow(mph, 0.16)) + (0.4275 * tf * math.pow(mph, 0.16))

        if (tf <= 50.0) and (mph >= 5.0):
            return round((wc - 32) / 1.8, 1)
        else:
            return t

    def Heatindex(self, t, h):
        tf = (t * 1.8) + 32
        c1 = -42.379
        c2 = 2.04901523
        c3 = 10.1433127
        c4 = -0.22475541
        c5 = -6.83783 * math.pow(10, -3)
        c6 = -5.481717 * math.pow(10, -2)
        c7 = 1.22874 * math.pow(10, -3)
        c8 = 8.5282 * math.pow(10, -4)
        c9 = -1.99 * math.pow(10, -6)

        hi = (c1 + (c2 * tf) + (c3 * h) + (c4 * tf * h) + (c5 * tf *tf) + (c6 * h * h) + (c7 * tf * tf * h) + (c8 * tf * h * h) + (c9 * tf * tf * h * h))

        if (tf < 80.0) or (h < 40.0):
            return t
        else:
            return round((hi - 32) / 1.8, 1)

    def setDriver(self, driver, value):
        if (self.units == "us"):
            value = (value * 1.8) + 32  # convert to F

        super(TemperatureNode, self).setDriver(driver, round(value, 1), report=True, force=True)



class HumidityNode(polyinterface.Node):
    id = 'humidity'
    hint = 0xffffff
    units = 'metric'
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 22}]

    def SetUnits(self, u):
        self.units = u

    def setDriver(self, driver, value):
        super(HumidityNode, self).setDriver(driver, value, report=True, force=True)

class PressureNode(polyinterface.Node):
    id = 'pressure'
    hint = 0xffffff
    units = 'metric'
    drivers = [ ]
    mytrend = []


    def SetUnits(self, u):
        self.units = u

    # convert station pressure in millibars to sealevel pressure
    def toSeaLevel(self, station, elevation):
        i = 287.05
        a = 9.80665
        r = 0.0065
        s = 1013.35 # pressure at sealevel
        n = 288.15

        l = a / (i * r)
        c = i * r / a
        u = math.pow(1 + math.pow(s / station, c) * (r * elevation / n), l)

        return (round((station * u), 3))

    # track pressures in a queue and calculate trend
    def updateTrend(self, current):
        t = 0
        past = 0

        if len(self.mytrend) == 180:
            past = self.mytrend.pop()

        if self.mytrend != []:
            past = self.mytrend[0]

        # calculate trend
        if ((past - current) > 1):
            t = -1
        elif ((past - current) < -1):
            t = 1

        self.mytrend.insert(0, current)
        return t

    # We want to override the SetDriver method so that we can properly
    # convert the units based on the user preference.
    def setDriver(self, driver, value):
        if (self.units == 'us'):
            value = round(value * 0.02952998751, 3)
        super(PressureNode, self).setDriver(driver, value, report=True, force=True)


class WindNode(polyinterface.Node):
    id = 'wind'
    hint = 0xffffff
    units = 'metric'
    drivers = [ ]

    def SetUnits(self, u):
        self.units = u

    def setDriver(self, driver, value):
        if (driver == 'ST' or driver == 'GV1' or driver == 'GV3'):
            # Metric value is meters/sec (not KPH)
            if (self.units != 'metric'):
                value = round(value * 2.23694, 2)
        super(WindNode, self).setDriver(driver, value, report=True, force=True)

class PrecipitationNode(polyinterface.Node):
    id = 'precipitation'
    hint = 0xffffff
    units = 'metric'
    drivers = [ ]
    hourly_rain = 0
    daily_rain = 0
    weekly_rain = 0
    monthly_rain = 0
    yearly_rain = 0

    prev_hour = 0
    prev_day = 0
    prev_week = 0

    def SetUnits(self, u):
        self.units = u

    def hourly_accumulation(self, r):
        current_hour = datetime.datetime.now().hour
        if (current_hour != self.prev_hour):
            self.prev_hour = current_hour
            self.hourly = 0

        self.hourly_rain += r
        return self.hourly_rain

    def daily_accumulation(self, r):
        current_day = datetime.datetime.now().day
        if (current_day != self.prev_day):
            self.prev_day = current_day
            self.daily_rain = 0

        self.daily_rain += r
        return self.daily_rain

    def weekly_accumulation(self, r):
        current_week = datetime.datetime.now().day
        if (current_weekday != self.prev_weekday):
            self.prev_week = current_weekday
            self.weekly_rain = 0

        self.weekly_rain += r
        return self.weekly_rain

        
    def setDriver(self, driver, value):
        if (self.units == 'us'):
            value = round(value * 0.03937, 2)
        super(PrecipitationNode, self).setDriver(driver, value, report=True, force=True)

class LightNode(polyinterface.Node):
    id = 'light'
    units = 'metric'
    hint = 0xffffff
    drivers = [ ]

    def SetUnits(self, u):
        self.units = u

    def setDriver(self, driver, value):
        super(LightNode, self).setDriver(driver, value, report=True, force=True)

class LightningNode(polyinterface.Node):
    id = 'lightning'
    hint = 0xffffff
    units = 'metric'
    drivers = [ ]

    def SetUnits(self, u):
        self.units = u

    def setDriver(self, driver, value):
        if (driver == 'GV0'):
            if (self.units != 'metric'):
                value = round(value / 1.609344, 1)
        super(LightningNode, self).setDriver(driver, value, report=True, force=True)


if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('MeteoBridge')
        """
        Instantiates the Interface to Polyglot.
        """
        polyglot.start()
        """
        Starts MQTT and connects to Polyglot.
        """
        control = Controller(polyglot)
        """
        Creates the Controller Node and passes in the Interface
        """
        control.runForever()
        """
        Sits around and does nothing forever, keeping your program running.
        """
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
        """
        Catch SIGTERM or Control-C and exit cleanly.
        """
