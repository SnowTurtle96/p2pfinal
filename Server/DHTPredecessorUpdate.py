'''
    File name: DHTPredecessorUpdate.py
    Author: Jamie Clarke
    Date last modified: 18/03/2019
    Python Version: 3.7
'''

import logging

from twisted.internet.protocol import ClientFactory, Protocol


class DHTPredecessorUpdateProtocol(Protocol):

    def connectionMade(self):
        # Grab the message that is being stored in the factory class
        data = self.factory.data

        # Append our network command to the message
        msgCMD = "==UPDATEPREDECESSOR=="

        # Convert our message to string and then convert the string to bytes
        msg = msgCMD + str(data)
        messageToSend = bytes(msg, 'utf-8')

        # Write our message over the established TCP transport
        self.transport.write(messageToSend)

        logging.info("Sending a DHT update to our predecessor")

    def dataReceived(self, data):
        logging.info("DHT has been updated")


class DHTPredecessorUpdate(ClientFactory):
    # Instantiate the protocol
    protocol = DHTPredecessorUpdateProtocol

    # On initialize of the factory class data passed is stored to a local variable
    def __init__(self, data):
        self.data = data
