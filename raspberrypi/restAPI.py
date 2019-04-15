'''
@author: s153571
Used to communicate with openhab through HTTP requests
'''

import requests
import globals
import json
import time
import generalFuncs


############################################
# HTTP REST API COMMUNICATION WITH OPENHAB #
############################################

#sets item state using HTTP request
#Gets called when a message is received over mqtt with the key-value pair "type" : "item"
def setItemState(jsonData, mqttClient):
    itemName = jsonData['itemName']
    pushState = jsonData['state']
    url = 'http://localhost:8080/rest/items/' + itemName
    headers = {'Content-Type': 'text/plain', 'Accept' : 'application/json'}
    response = requests.post(url, headers = headers, data = str(pushState))

    if response.status_code > 299:
        mqttClient.publish("error", "setItemState: " + str(response.status_code) )

#connect to device (thing) given a thingUID
#Gets called when a message is received over mqtt with the key-value pair "type" : "deviceConnect"
def connectToDevice(thingUID, mqttClient):

    #make sure the device appears in the inbox before trying to connect to it
    searchInbox(getBindings())
    url = 'http://localhost:8080/rest/inbox/' + thingUID + '/approve'
    headers = {'Content-Type': 'text/plain', 'Accept' : 'application/json'}
    response = requests.post(url, headers = headers)

    for thing in globals.devicesSaved:
        if thing['thingUID'] == thingUID:
            thing['status'] = 'connected' 

    #if http request doesn't work
    if response.status_code > 300:
        mqttClient.publish("error", "connectToDevice: " + str(response.status_code))


#disconnect a device (thing) given a thingUID
#Gets called when a message is received over mqtt with the key-value pair "type" : "deviceDisconnect"
def disconnectDevice(thingUID, mqttClient):
    url = 'http://localhost:8080/rest/things/' + thingUID + "?force=true"
    headers = {'Content-Type': 'text/plain', 'Accept' : 'application/json'}
    response = requests.delete(url, headers = headers)

    for thing in globals.devicesSaved:
        if thing['thingUID'] == thingUID:
            thing['status'] = 'unconnected'

    #if http request doesn't work
    if response.status_code > 300:
        mqttClient.publish("error", "disconnectDevice: " + str(response.status_code))


##################
#Helper functions#
##################

#Get unconnected devices from openhab inbox.
#gets called every 20 secs from main
def saveAndPublishNewDevicesUnconnected(mqttClient, newDevicesConnected ):

    #search for new devices with the bindings we have installed
    searchInbox(getBindings())

    url = 'http://localhost:8080/rest/inbox'
    headers = {'Content-Type': 'text/plain', 'Accept' : 'application/json'}
    response = requests.get(url,headers = headers)
    
    #if request worked
    if response.status_code < 300:
        inbox = json.loads(response.text)
        jsonData = simplifyJsonDevice(inbox,'thingUID','request', 'waiting')
        newDevices, globals.devicesSaved = returnNewAndUpdatedList(jsonData,globals.devicesSaved)

        for device in newDevicesConnected:
            newDevices.append(device)
        
        #if new devices publish them
        if len(newDevices) > 0:
            return newDevices
    else:
        mqttClient.publish("error", "publishUnconnectedDevice: " + str(inbox.status_code) )
                        
#get connected devices (things) from openhab and updates the list of devices
#gets called every 20 secs from main
def saveAndReturnNewDevicesConnected(mqttClient):
    url = 'http://localhost:8080/rest/things'
    headers = {'Content-Type': 'text/plain', 'Accept' : 'application/json'}
    response = requests.get(url,headers = headers)


    #if http request works
    if response.status_code < 300:
        things = json.loads(response.text)
        thingsSimple = simplifyJsonDevice(things,'UID','request','connected')
        thingsActuators = insertActuators(mqttClient, things, thingsSimple)
        newDevices, globals.devicesSaved = returnNewAndUpdatedList(thingsActuators,globals.devicesSaved)
        return newDevices
    

    #if http request doesn't work
    else:
        mqttClient.publish("error", "publishConnectedDevices: " + str(things.status_code))


#gets all items from openhab
#gets called everytime data is saved from sensors, and when a device is connected
def getAllItems(mqttClient):
    url = "http://localhost:8080/rest/items"
    headers = {'Content-Type': 'text/plain', 'Accept' : 'application/json'}
    response=requests.get(url, headers = headers)

    #if http request is alright
    if response.status_code < 300:
        items = json.loads(response.text)
        return items
    #if http request doesn't work
    else:
        mqttClient.publish("error", "items: " + str(response.status_code)  )
        return None


#Simplifies the json data received from openhab-
#for unconnected devices the keyword is thingUID, for connected it is UID
#gets called when device json data is received from openhab
def simplifyJsonDevice(things,thingUID, request, status):
    jsonData = [] #store device UIDs and device labels in this badboy
    for thing in things:
        updateJSON = {
            'thingUID': thing[thingUID],
            'label': thing['label'],
            'items': [],
            'status': status,
            'hubID' : globals.hubID
        }
        jsonData.append(updateJSON)
    return jsonData


#Compares 2 lists and spits out new entries, along with an updated list 
#Gets called every 20 secs when we compare the list of devices from openhab with the saved list
def returnNewAndUpdatedList(updatedEntries,savedEntries):
    newEntries =  []
    existBool = False    
    for updatedEntry in updatedEntries:
        for savedEntry in savedEntries:
            if updatedEntry['label'] == savedEntry['label']:
                existBool = True

        if existBool == False: #if the entry did not appear on the list, existBool will be false
            newEntries.append(updatedEntry)
        existBool = False
    
    for newEntry in newEntries:
        savedEntries.append(newEntry)
    
    return newEntries, savedEntries


#get UUID of openhub - used for having a unique id for the RP
#Gets called in the beginning of the program to get the uuid of the openhab installation
def getUUID():
    url = "http://localhost:8080/rest/uuid"
    headers = {'Accept' : 'text/plain'}
    response = requests.get(url,headers = headers)

    #if request worked
    if response.status_code < 300:
        uuid = response.text
        return uuid


#only used for testing, where we send devices every 30 secs.
def publishDevicesTesting(mqttClient):

    seconds = generalFuncs.getSecondsAndMinutes()[0]
    if seconds % 30 == 0:
        mqttClient.publish("devices",json.dumps(globals.devicesSaved))
        time.sleep(1)

#Gets all the bindings installed in openhab
#gets called when we search for devices in the openhab inbox
def getBindings():
    url = 'http://localhost:8080/rest/bindings'
    headers = {'Content-Type': 'text/plain', 'Accept' : 'application/json'}
    response = requests.get(url,headers = headers)

    #if HTTP request works
    if response.status_code < 300:
        bindings = json.loads(response.text)
        return bindings

#search inbox for devices using installed bindings
#gets called every time we search for a device (every 20 secs)
def searchInbox(bindings):
    for binding in bindings:
        bindingID = binding['id']
        url = 'http://localhost:8080/rest/discovery/bindings/' + bindingID + '/scan'
        headers = {'Content-Type': 'application/json', 'Accept' : 'text/plain'}
        requests.post(url,headers = headers)
        time.sleep(0.4)

#Used for linking an item together with a thing in our list.
#Gets called every time 
def getActuatorForThing(item):
    jsonData = {
        'itemName' : item['name'],
        'readOnly' : item['stateDescription']['readOnly'],
        'state' : generalFuncs.takeOutNumber(item['state']),
        'label' : item['label']
    }
    return jsonData

#inserts actuators in things that have them 
#gets called every 20 seconds, to make sure that all devices have actuators listed
def insertActuators(mqttClient,things,thingsSimple):
    items = getAllItems(mqttClient)
    
    #pull out all items that are actuators and their names
    actuators = []
    actuatorNames = []
    for item in items:
        if 'stateDescription' in item and item['stateDescription']['readOnly'] == False:
            actuators.append(item)
            actuatorNames.append(item['name'])


    #Find the thing that contains the item
    for thing in things:
        for channel in thing['channels']:
            if len(channel['linkedItems']) > 0 and channel['linkedItems'][0] in actuatorNames:
                
                #store the item in the thingsSimple list
                for thingSimple in thingsSimple:
                    if thing['UID'] == thingSimple['thingUID']:
                        ind = actuatorNames.index(channel['linkedItems'][0])
                        apActuator = getActuatorForThing(actuators[ind])
                        thingSimple['items'].append(apActuator)


    return thingsSimple