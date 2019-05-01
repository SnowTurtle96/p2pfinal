'''
    File name: StateChecks.py
    Author: Jamie Clarke
    Date last modified: 18/03/2019
    Python Version: 3.7
'''

from pathlib import Path

"""

Python file that can be imported that provides checks on the systems state     

"""


def checkDHTInitialized():
    my_file = Path("DHT.json")
    if my_file.is_file():
        return True
    else:
        return False

def checkSessionExists():
    my_file = Path("messagingPartner.json")
    if (my_file.is_file()):
        return True
    else:
        return False
