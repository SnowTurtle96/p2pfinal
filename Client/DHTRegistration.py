'''
    File name: DHTRegistration.py
    Author: Jamie Clarke
    Date last modified: 18/03/2019
    Python Version: 3.7
'''

import logging

from twisted.internet.protocol import ClientFactory, Protocol


class DHTProtocol(Protocol):
    """

      DHT protocol class handles the TCP connection to the network along with appending the necessary protocol information.

    """

    # This may be considered the initializer of the protocol, because it is called when the connection is completed.
    # This is called once the connection to the server has been established;
    def connectionMade(self):
        # Grab the message that is being stored in the factory class
        data = self.factory.data

        # Set our network CMD
        msgCMD = "==REGISTER=="

        # Convert our message to string and then convert the string to bytes
        msg = msgCMD + str(data)
        messageToSend = bytes(msg, 'utf-8')

        # Send this message across the established TCP connection
        self.transport.write(messageToSend)

        # Use our global logger to alert the user that there message is being sent
        userInfo = logging.getLogger("1")
        logging.info("Sending a DHT request to register to network!")


class DHTRegistration(ClientFactory):
    # Instantiate the protocol
    protocol = DHTProtocol

    # On initialize of the factory class data passed is stored to a local variable
    def __init__(self, data):
        self.data = data
