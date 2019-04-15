"""
@author: Søren Møller Christensen
This is the main script used to control everything in the hub.
"""

import time
from datetime import datetime
import hub
from influxdb import InfluxDBClient
import json
import globals
import restAPI


globals.init() #this initiates the globals

#all the following values needs to be set 
mqttBroker = "se2-webapp05.compute.dtu.dk"
mqttPort = 1883
influxHost = 'localhost'
influxPort = '8086'
influxUsername = 'admin'
influxPassword = 'abc'
influxDatabase = 'openhab'

#initialize mqtt client 
mqttClient = hub.initMQTT(mqttBroker,mqttPort)
#initialize influx client
influxClient = InfluxDBClient(influxHost,influxPort, influxUsername, influxPassword, influxDatabase)
mqttClient.loop_start()

#This is the main part of the program - runs forever
while True:
    if globals.hubConnected == False:
        hub.connectToServer(mqttClient)
    while globals.hubConnected == True:
        hub.saveDataEveryFiveMinutes(influxClient, mqttClient)
        hub.publishDataEveryHalfHour(influxClient, mqttClient)
        hub.publishAndSaveNewDevicesEvery20secs(mqttClient)
        hub.publishStayAlive(mqttClient)
