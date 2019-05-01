'''
    File name: DHTSearch.py
    Author: Jamie Clarke
    Date last modified: 18/03/2019
    Python Version: 3.7
'''

import logging

from twisted.internet.protocol import ClientFactory, Protocol


class DHTSearchProtocol(Protocol):
    """

    DHT Search Protocol class handles the TCP connection to the network and appends the necessary protocol information

    """

    # This may be considered the initializer of the protocol, because it is called when the connection is completed.
    # This is called once the connection to the server has been established;
    def connectionMade(self):
        # Grab the message that is being stored in the factory class
        data = self.factory.data

        # Set our network CMD
        msgCMD = "==SEARCH=="

        # Append our network command to the message
        msg = msgCMD + str(data)
        messageToSend = bytes(msg, 'utf-8')

        # Write our message over the established TCP transport
        self.transport.write(messageToSend)

        # Use our global logger to alert the user that connection was established and our message was sent
        userInfo = logging.getLogger("1")
        logging.info("Sending a DHT search request to find user" + str(data))





class DHTSearch(ClientFactory):
    # Instantiate the protocol
    protocol = DHTSearchProtocol

    # On initialize of the factory class data passed is stored to a local variable
    def __init__(self, data):
        self.data = data
