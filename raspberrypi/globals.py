'''
@author: Søren Møller Christensen
Used to initialize global values
'''

import requests
import json
import restAPI

#initializes global values.
#Only the hubID is constant
#gets initialized in the beginning of main
def init():
    global hubConnected
    hubConnected = False
    global hubID
    hubID = restAPI.getUUID()
    global devicesSaved
    devicesSaved = []
    