import logging

from twisted.internet.protocol import Protocol, ClientFactory


class DHTSearchReturnProtocol(Protocol):

    def connectionMade(self):
        # Grab the message that is being stored in the factory class
        data = self.factory.data
        # Append our network command to the message
        msgCMD = "==SEARCHRETURN=="
        # Convert our message to string and then convert the string to bytes
        msg = msgCMD + str(data)
        messageToSend = bytes(msg, 'utf-8')

        # Write our message over the established TCP transport
        self.transport.write(messageToSend)
        logging.info("Found data requested from the DHT search sending" + str(data))

    def dataReceived(self, data):
        logging.info("DHT has been updated")


class DHTSearchReturn(ClientFactory):
    # Instantiate the protocol
    protocol = DHTSearchReturnProtocol

    # On initialize of the factory class data passed is stored to a local variable
    def __init__(self, data):
        self.data = data