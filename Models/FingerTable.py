'''
    File name: FingerTable.py
    Author: Jamie Clarke
    Date last modified: 29/03/2019
    Python Version: 3.7
'''

from Models.User import User


class FingerTable():
    """

    Finger table holds User() objects for each of our DHT neighbours.

    Attributes:
        successor -          Stores our successor in the DHT
        predecessor -        Stores our predecessor in the DHT
        nodeid -             Stores out nodeID generated from our username
        finger1 -            NOT IMPLEMENTED
        finger2 -            NOT IMPLEMENTED

    """

    successor = None
    predecessor = None
    nodeid = None
    finger1 = None
    finger2 = None

    # Convert this object into type dictionary. Each attribute is assigned to key/value pairs
    def toDict(self):
        return {"successor": self.successor, "predecessor": self.predecessor, "nodeid": self.nodeid}

    # When a finger table is initalzied set each attribute to a blank user. This prevents undefined errors
    def __init__(self):
        user = User().toDict()
        self.successor = user
        self.predecessor = user
        self.nodeid = user
        self.finger1 = user
        self.finger2 = user
