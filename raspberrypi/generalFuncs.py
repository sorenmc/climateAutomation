'''
@author: Søren Møller Christensen
Functions that can be used more places
'''
import re #regular expressions
from datetime import datetime #used as timer...

#if the state contains any symbols other than the number, this is removed.
#returns an interger or a floating point number stored as a string
#gets called every time we store sensor data
def takeOutNumber(state):
    state = str(state)

    #matches a floating point number or an integer
    regex = '([-+]?[0-9]+\.?[0-9]*)|NULL'
    match = re.search(regex,state)

    #takes out the first match eg:  '3.3 c 333' would match '3.3'
    output = match.group()
    return output

#returns seconds and minutes of the internal clock in the computer.
#This is used to time the functions - can be used since we do not need high precission.
def getSecondsAndMinutes():
    date = datetime.now()
    seconds = date.second
    minutes = date.minute
    return seconds, minutes