'''
    File name: Server.py
    Author: Jamie Clarke
    Date last modified: 20/03/2019
    Python Version: 3.7
'''
import ast
import json
import logging

from twisted.internet import protocol

from Encryption.AsymmetricEncryption import AsymmetricEncryption
from Networking.DHTAlgorithm import DHTAlgoirthm
from Networking.OR import OR
from Utils import StateChecks

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.FileHandler("{0}/{1}.log".format("./", "client")),
        logging.StreamHandler()
    ])
logger = logging.getLogger(),

"""
Server class handles incoming requests over the network
Attributes:
    debuggingWindow -       Allows loggging to be displayed in the tkinter UI to the user
    dhtAlgorithms -         Instantiates DHT Algorithms used for handling DHT network requests
    initialChecks -         Utility library that determines that state of server on launch
    onionRouter -           Instantiates an onion router for routing requests
"""

class Server(protocol.Protocol):
    # Instantiations and creation of debugging logger
    debuggingWindow = logging.getLogger("1")
    dhtAlgorithms = DHTAlgoirthm()
    initialChecks = StateChecks
    onionRouter = OR()

    logging.info("Server has been initialized!")

    # Determine if a DHT has been initialized previously on this PC
    if (initialChecks.checkDHTInitialized()):
        dhtAlgorithms.dht.loadDHTInformation()

    # The core of the server module. Callback for when data is recieved. Determines which network command is present and executes the associated method
    def dataReceived(self, data):
        logging.info("Node connecting")
        debuggingWindow = logging.getLogger("1")
        debuggingWindow.info("Incoming Data")
        data = data.decode('utf-8')
        logging.info(data)

        # Determine which network command is present from the protocol
        if "==REGISTER==" in data:
            # A request has been recieved to bootstrap a new node into the network. Perform a search to determine if this request can be satified by the local node
            debuggingWindow.info("Node registered")
            self.dhtAlgorithms.DHTPositionSearch(data)

        elif "==CREATE==" in data:
            # Call onionrouter to save this AES key. Register the current node as a onion router

            debuggingWindow.info("Recieved a symmetric key")
            transport = self.transport.getPeer().host
            self.onionRouter.recieveORKey(data, transport)

            # Send ACK
            reply = "==KEYRECIEVED=="
            self.transport.write(reply.encode('utf=8'))


        elif "==UPDATESUCCESSOR==" in data:
            # A network stabilisation request has notified us that our successor has changed. The new successor is included within the data variable
            debuggingWindow.info("Another node is updating our successor")
            # Remove the network command from the message
            data = data.replace('==UPDATESUCCESSOR==', '')
            data = data.replace('\'', '"')
            data = json.loads(data)

            # Use DHT algorithms instantiation of the DHT class to update the successor
            self.dhtAlgorithms.dht.updateSuccessor(data)


        elif "==UPDATEPREDECESSOR==" in data:
            # A network stabilisation request has notified us that our predecessor has changed. The new predecessor is included within the data variable
            debuggingWindow.info("Another node is updating our predecessor")
            # Remove the network command from the message
            data = data.replace('==UPDATEPREDECESSOR==', '')
            data = data.replace('\'', '"')
            data = json.loads(data)

            # Use DHT algorithms instantiation of the DHT class to update the predecessor
            self.dhtAlgorithms.dht.updatePredecessor(data)


        elif "==REGISTERRETURN==" in data:
            # The bootstrapping process has been completed. A node on the DHT successfully postioned the node and has returned a copy of the local nodes routing table
            debuggingWindow.info("DHT RETURN FROM A LONG RANGE NODE")
            # Replace the network command
            data = data.replace('==REGISTERRETURN==', '')
            data = data.replace('\'', '"')
            data = json.loads(data)
            # Load the received network information into our local DHT class
            self.dhtAlgorithms.dht.DHTPackageFromExternalNode(data)



        elif "==SEARCHRETURN==" in data:
            # A search for a users contact information on the network has been returned. You are now capable of messaging that user
            debuggingWindow.info(
                "A node has found the user from your search and has returned it to you. Messaging now enabled")
            # Replace the network commmand
            data = data.replace("==SEARCHRETURN==", '')
            data = data.replace('\'', '"')
            data = json.loads(data)
            # Outsource the configuration process of establishing a messaging session with our messaging partner to the DHT class
            self.dhtAlgorithms.dht.DHTSearchReturn(data)

        elif "==SEARCH==" in data:
            # A request has been recieved to search our local storage for a SHA256 value
            debuggingWindow.info("REQUEST RECEIVED FOR A SEARCH OF OUR STORAGE")
            data = data.replace("==SEARCH==", '')

            self.dhtAlgorithms.DHTInformationSearch(data)

        # If no networking command is present then this implies it is an onion circuit message
        else:
            debuggingWindow.info("Onion Networking")
            asymmetricEncryption = AsymmetricEncryption()
            reencoded = {}
            reencoded['CMD'] = "None"

            # Try RSA decryption
            try:
                reencoded = ast.literal_eval(data)
                reencoded['CMD'] = asymmetricEncryption.decrypt("t", reencoded['CMD'])
                reencoded['CMD'] = reencoded['CMD'].decode('utf-8')

            # Message is not encoded with RSA, means it an onion message
            except:
                # Return the reencoded variable back to its initial state
                reencoded = {}
                reencoded['CMD'] = "None"
                logging.info("Not encrypted with RSA")

            # Check if the encrypted message is a RSA encrypted onion key

            if "==CREATE==" in reencoded['CMD']:
                debuggingWindow.info("Recieved a symmetric key")
                transport = self.transport.getPeer().host
                self.onionRouter.recieveORKey(reencoded, transport)

                # Send ACK
                reply = "==KEYRECIEVED=="
                self.transport.write(reply.encode('utf=8'))

            # Message is not encrypted with RSA means it must be an AES onion message
            else:
                self.onionRouter.router(data)
