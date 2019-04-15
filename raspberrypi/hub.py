'''
@author: Søren Møller Christensen
Influxdb and mqtt functions
'''


import paho.mqtt.client as  mqtt #mqtt communication
from influxdb import InfluxDBClient #communication with influxdb
import json
import time #used for pausing program.
import sys #exception handling
import globals #globals are stored in this file
import restAPI # communication with openhab
import generalFuncs #general functions
from datetime import datetime # used to get time stamp for influx

#################################################
# INFLUX DATABASE COMMUNICATION USED IN PROGRAM #
#################################################


#Saves sensor data from openhab every 5 seconds in the influxdb on the hub
#gets called in main
def saveDataEveryFiveMinutes(influxClient, mqttClient):
        seconds, minutes = generalFuncs.getSecondsAndMinutes()
        if minutes % 5 == 0 and seconds == 0:
            saveNewData(influxClient, mqttClient)
            time.sleep(1)


#publishes data from influxdb to mqtt every half hour
#gets called in main
def publishDataEveryHalfHour(influxClient,mqttClient):
        seconds, minutes = generalFuncs.getSecondsAndMinutes()

        if minutes % 30 == 0 and seconds == 2:
            jsonString = returnInfluxData(influxClient)
            mqttClient.publish("data",jsonString)
            deleteInfluxData(influxClient)
            time.sleep(1)


###########################
#Influx helper functions###
###########################

#saves the new data from openhab
#gets called every 5 minutes - helper function
def saveNewData(influxClient, mqttClient):

    items = restAPI.getAllItems(mqttClient)

    #only save netatmo sensor Data
    try:
        jsonData = logDataInJson(items)

        influxClient.write_points(jsonData)
        print("Write points: {0}".format(jsonData))
        
    except:
        e = sys.exc_info()[0]
        print("influx error: " + str(e))

#returns current data stored in the influx database
#gets called when we publish data on mqtt every 30 mins
def returnInfluxData(influxClient):
    ifqlString = "SELECT * from sensorData"
    rs = influxClient.query(ifqlString)
    jsonData = list(rs.get_points(measurement = 'sensorData'))
    return json.dumps(jsonData)

#deletes all data in the influxdb
#gets called every time we send the data over mqtt
def deleteInfluxData(influxClient):
    ifqlString = "DROP MEASUREMENT sensorData"
    influxClient.query(ifqlString)
    print("Data deleted from influx")

#Takes data from items and stores it as json data ready for storage in the influxdb
#gets called every time we save data
def logDataInJson(items):
    date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

    keyValuePairs = {}

    for item in items:
        if 'state' in item:
            itemState = generalFuncs.takeOutNumber(item["state"])
            keyValuePairs[item["label"]] = itemState


    jsonData = [
        {
            "measurement": 'sensorData',
            "tags":{ "hubID": globals.hubID
            },
            "time": date,
            "fields": keyValuePairs
        }
    ]
    return jsonData


##########################
#FUNCTIONS USED FOR MQTT #
##########################

#initializes the mqtt client.
#gets called on start up
def initMQTT(mqttBroker, mqttPort):
    #client initialization, clean session = False means we remember subscribtions if we reconnect
    mqttClient =  mqtt.Client(client_id = globals.hubID, clean_session = True)

    #add callback functions to client
    mqttClient.on_log = on_log
    mqttClient.on_connect = on_connect
    mqttClient.on_subscribe = on_subscribe
    mqttClient.on_message = on_message


    #Connect to broker
    print("trying to connect to broker: " + mqttBroker)
    mqttClient.connect(mqttBroker,port = mqttPort)
    #mqttClient.loop_start()
    time.sleep(4)
    return mqttClient

#Depending on the messages key "type"s value
#an action will be performed
def onMessageActions(mqttClient, topic, mes):

    mesJson = json.loads(mes)

    #sets the state of an item
    if mesJson['type'] == 'hubConnect':
        globals.hubConnected = True
    elif mesJson['type'] == 'hubDisconnect':
        globals.hubConnected = False
    elif mesJson['type'] == 'item':
        restAPI.setItemState(mesJson,mqttClient)

    #connects to device with thingUID contained    
    elif mesJson['type'] == 'deviceConnect':
        restAPI.connectToDevice(mesJson['thingUID'],mqttClient)

    #disconnects device with thingUID contained in the message
    elif mesJson['type'] == 'deviceDisconnect':
        restAPI.disconnectDevice(mesJson['thingUID'],mqttClient)

#publish unconnected and connected devices every 20 seconds
#gets called in main
def publishAndSaveNewDevicesEvery20secs(mqttClient):

    seconds  = generalFuncs.getSecondsAndMinutes()[0]#only get seconds
    if seconds % 20 == 0:
        
        newDevices = restAPI.saveAndReturnNewDevicesConnected(mqttClient)
        newDevices = restAPI.saveAndPublishNewDevicesUnconnected(mqttClient, newDevices)
        if newDevices != None:
            mqttClient.publish('devices', json.dumps(newDevices))
        time.sleep(1)


#publishes a stay alive message 2 times per minute
#this is to secure that the webapp knows which hubs are online
#called in main
def publishStayAlive(mqttClient):
    seconds = generalFuncs.getSecondsAndMinutes()[0]
    if seconds % 25 == 0:
        jsonData = {
            'hubID' : globals.hubID
        }
        mqttClient.publish('alive', json.dumps(jsonData))
        time.sleep(1)


#sends the hubID to the hubs topic - used for connecting to the device.
#gets called in main
def connectToServer(mqttClient):
    seconds = generalFuncs.getSecondsAndMinutes()[0]

    if seconds % 20 == 0:
        jsonData = {
            'hubID': globals.hubID
        }
        mqttClient.publish('hubs',json.dumps(jsonData) )
        time.sleep(1)


####################
#CALLBACK functions#
####################


#callback fuction used for logging
#gets called everytime the mqtt client does anything
def on_log(client,userdata,level,buf):
    print("log: " + buf)


#the functions subscribes to the topic that is the hubID 
#(taken from openhabs UUID) when the client connects to a broker
#gets called every time the mqtt client connects to a broker
def on_connect(client, userdata,flags,rc):
    #rc = return code, 0 means accepted
    if rc == 0:
        print("Connection ok")
        client.subscribe(globals.hubID)
    else:
        print("Bad connection, rc = ", rc)


# The function takes action depending on the value of the key "type" 
# gets called everytime a message is received
def on_message(client, userdata, message):
    mes = str(message.payload.decode("utf-8"))
    topic = message.topic
    #used for debugging
    print("message received " , mes)
    print("message topic: ", topic)

    #actual action
    onMessageActions(client,topic, mes)


# When the client subscribes to a topic, it will print out the 
# topic and quality of service.
def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))




