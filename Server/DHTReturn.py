'''
    File name: DHTReturn.py
    Author: Jamie Clarke
    Date last modified: 18/03/2019
    Python Version: 3.7
'''
import logging

from twisted.internet.protocol import ClientFactory, Protocol


class DHTReturnProtocol(Protocol):

    def connectionMade(self):
        # Grab the message that is being stored in the factory class
        data = self.factory.data

        # Append our network command to the message
        msgCMD = "==REGISTERRETURN=="

        # Convert our message to string and then convert the string to bytes
        msg = msgCMD + str(data)
        messageToSend = bytes(msg, 'utf-8')

        # Write our message over the established TCP transport
        self.transport.write(messageToSend)
        logging.info("Sending DHT information back to the person who requested")


class DHTReturn(ClientFactory):
    # Instantiate the protocol
    protocol = DHTReturnProtocol

    # On initialize of the factory class data passed is stored to a local variable
    def __init__(self, data):
        self.data = data
