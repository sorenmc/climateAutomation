
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 30 15:45:53 2018

@author: SORENMC
"""
#pip install influxdb
import time
from datetime import datetime
import hub
from influxdb import InfluxDBClient
import json
import globals

#itemName = 'ZWaveNode2LCZ251LivingConnectZThermostat251_SetpointHeating'
globals.init() #this initiates the globals
mqttBroker = "se2-webapp05.compute.dtu.dk"
mqttPort = 1883
influxHost = 'localhost'
influxPort = '8086'
influxUsername = 'admin'
influxPassword = 'abc'
influxDatabase = 'openhab'
mqttClient = hub.initMQTT(mqttBroker,mqttPort)
influxClient = InfluxDBClient(influxHost,influxPort, influxUsername, influxPassword, influxDatabase)
mqttClient.loop_start()
mqttClient.subscribe(globals.hubID)


while True:
    if globals.hubConnected == False:
        hub.connectToServer(mqttClient)
    while 1:
        hub.publishConnectedDevices(mqttClient)
        time.sleep(3)
        hub.saveDataEveryFiveMinutes(influxClient, mqttClient)
        hub.publishDataEveryHalfHour(influxClient, mqttClient)
        hub.publishDevicesEvery20Secs(mqttClient)
