'''
    File name: MessageFactory.py
    Author: Jamie Clarke
    Date last modified: 18/03/2019
    Python Version: 3.7
'''

from twisted.internet.protocol import ClientFactory, Protocol


class MessageProtocol(Protocol):
    """

     DHT Message Protocol class handles the TCP connection to the network and appends the necessary protocol information for sending a message to another user

     """

    # This may be considered the initializer of the protocol, because it is called when the connection is completed.
    # This is called once the connection to the server has been established;
    def connectionMade(self):
        # Grab the message that is being stored in the factory class
        data = self.factory.data
        # Write message over the established TCP transport
        self.transport.write(data)




class MessageFactory(ClientFactory):
    # Instantiate the protocol
    protocol = MessageProtocol

    # On initialize of the factory class data passed is stored to a local variable
    def __init__(self, data):
        self.data = data
