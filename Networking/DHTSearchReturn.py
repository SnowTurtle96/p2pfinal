'''
    File name: DHTSearchReturn.py
    Author: Jamie Clarke
    Date last modified: 18/03/2019
    Python Version: 3.7
'''

import logging

from twisted.internet.protocol import ClientFactory, Protocol


class DHTSearchReturnProtocol(Protocol):

    def connectionMade(self):
        # Grab the message that is being stored in the factory class
        data = self.factory.data

        # Append our network command to the message
        msgCMD = "==SEARCHRETURN=="

        # Convert our message to string and then convert the string to bytes
        msg = msgCMD + str(data)
        messageToSend = bytes(msg, 'utf-8')

        # Send this message across the established TCP connection
        self.transport.write(messageToSend)

        logging.info("Found data requested from the DHT search sending" + str(data))

    def dataReceived(self, data):
        logging.info("DHT has been updated")


class DHTSearchReturn(ClientFactory):
    protocol = DHTSearchReturnProtocol

    def __init__(self, data):
        self.data = data