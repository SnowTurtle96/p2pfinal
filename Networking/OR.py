'''
    File name: OR.py
    Author: Jamie Clarke
    Date last modified: 18/03/2019
    Python Version: 3.7
'''

import ast
import json
import logging
import random
import time
import uuid
from pickle import dumps
from pickle import loads

from cryptography.fernet import Fernet
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory, Protocol

import Networking
import Networking
from Client.MessageFactory import MessageFactory
from Encryption.AsymmetricEncryption import AsymmetricEncryption
from Encryption.SymmetricEncryption import SymmetricEncryption
from Models.Route import Route

key1 = None
key2 = None
key3 = None
circuits = []
route = Route()
recieverIP = None
recieverPort = None
recieverPublicKey = None

class OR():
    """
    User class maintains information about the user and is also used by other nodes to contact eachother
    Attributes:
        recieverIP -          Stores the IP that this computer is operating on
        recieverPort -        Stores the port that the user has selected to open for listening by the server class
        encryptedMessage -    The resulting message after applying three layers of encryption
        key1 -                Symmetric key generated for hop1
        key2 -                Symmetric key generated for hop2
        key3 -                Symmetric key generated for recipient of the message
    """




    encryptedMessage = None
    symmetricEncryption = SymmetricEncryption()
    asymmetricEncryption = AsymmetricEncryption()
    """Before we create our onion route we need to know who we are sending our message to"""
    # This maintains the current circuits our node is involved in, allowing symmetric onion keys to be retained for more than one route.
    # We may want to conduct many chat sessions at once. By maintaining an array of reciever keys assigned to circuit IDs this will be possible.
    receiverKeys = []

    # Instantiate logger for the GUI debugging window
    debuggingWindow = logging.getLogger("1")
    routeID = None

    def constructRoute(self, peerList):

        randroute = random.randint(1,2)
        logging.info("Random route used random seed: " + str(randroute))
        if(randroute == 1):
            Networking.OR.route.hop1 = peerList['successor']
            Networking.OR.route.hop2 = peerList['predecessor']
        else:
            Networking.OR.route.hop1 = peerList['predecessor']
            Networking.OR.route.hop2 = peerList['successor']

        self.routeID = uuid.uuid4()

    def createOnionKeys(self):
        symmetricEncryption = SymmetricEncryption()
        Networking.OR.key1 = symmetricEncryption.createKeys()
        Networking.OR.key2 = symmetricEncryption.createKeys()
        Networking.OR.key3 = symmetricEncryption.createKeys()

    def exchangeKeys(self):
        # Generate keys using symmetric key class

        # Send the user some debugging information
        userInfo = logging.getLogger("1")
        userInfo.info("Exchanging Keys")

        # The protocol command that adds a node to an onion route
        CMD = b"==CREATE=="
        
        keyExchangeHop1 = {}
        # keyExchangeHop1['CIRCID'] = str(self.routeID)
        keyExchangeHop1['CMD'] = self.asymmetricEncryption.encrypt(route.hop1['publickey'],  CMD)
        keyExchangeHop1['KEY'] = self.asymmetricEncryption.encrypt(route.hop1['publickey'],  Networking.OR.key1)


        keyExchangeHop2 = {}
        # keyExchangeHop2['CIRCID'] = str(self.routeID)
        keyExchangeHop2['CMD'] = self.asymmetricEncryption.encrypt(route.hop2['publickey'],  CMD)
        keyExchangeHop2['KEY'] = self.asymmetricEncryption.encrypt(route.hop2['publickey'],  Networking.OR.key2)


        keyExchangeHop3 = {}
        # keyExchangeHop3['CIRCID'] = str(self.routeID)
        keyExchangeHop3['CMD'] = self.asymmetricEncryption.encrypt(self.recieverPublicKey,  CMD)
        keyExchangeHop3['KEY'] = self.asymmetricEncryption.encrypt(self.recieverPublicKey, Networking.OR.key3)

        # Convert each exchange dictionary into a string, this should then be converted into bytes using utf-8
        keyExchangePackage1 = bytes(str(keyExchangeHop1), 'utf-8')
        keyExchangePackage2 = bytes(str(keyExchangeHop2), 'utf-8')
        keyExchangePackage3 = bytes(str(keyExchangeHop3), 'utf-8')

        # Useful debugging information
        logging.info("Key Exchange Hop 1")
        logging.info(keyExchangeHop1)
        logging.info("Key Exchange Hop 2")
        logging.info(keyExchangeHop2)
        logging.info("Key Exchange for Reciever")

        logging.info(keyExchangeHop3)
        userInfo.info("First OR" + str(route.hop1["ip"]))

        # AES symmetric keys are sent to the circuit in anticpation for a message being sent
        reactor.connectTCP(route.hop1["ip"], int(route.hop1["port"]), MessageFactory(keyExchangePackage1))
        userInfo.info("Second OR" + str(route.hop2["ip"]))
        reactor.connectTCP(route.hop2["ip"], int(route.hop2["port"]), MessageFactory(keyExchangePackage2))
        userInfo.info("Receiver Exchange" + str(self.recieverPort) + str(self.recieverIP))
        reactor.connectTCP(self.recieverIP, int(self.recieverPort), MessageFactory(keyExchangePackage3))

    def encryptMsgForOnionRouting(msg):
        # Encrpytion is preformed First In Last Out
        # Reciever will be encrypted first working way back from OR3 TO OR1

        # This message is intended for the last hop/recipitent
        d3 = {"CIRCID": str(OR.routeID), "cmd": "MSG", "msg": msg}
        key3 = Fernet(Networking.OR.key3)
        token3 = key3.encrypt(dumps(d3))
        logging.info("VERIFY ENCRYPTION IS APPLIED PASS 1: " + str(d3))

        # This message is intended for the second hop/onion node
        d2 = {"CIRCID": str(OR.routeID), "cmd": "FWD", "ip": Networking.OR.recieverIP, "port": Networking.OR.recieverPort,
              "msg": token3}
        key2 = Fernet(Networking.OR.key2)
        token2 = key2.encrypt(dumps(d2))
        logging.info("VERIFY ENCRYPTION IS APPLIED PASS 2: " + str(d2))

        # This message is intended for the first hop/onion node
        d1 = {"CIRCID": str(OR.routeID), "cmd": "FWD", "ip": route.hop2['ip'], "port": route.hop2['port'],
              "msg": token2}
        key1 = Fernet(Networking.OR.key1)
        token1 = key1.encrypt(dumps(d1))
        logging.info("VERIFY ENCRYPTION IS APPLIED PASS 3: " + str(d1))

        OR.encryptedMessage = token1

    # Preparation for messaging a user recieved from the DHT requires it to be read in from file
    def loadInRecipitent():
        logging.info("Recipitent read in")

        # Open up the file and read the contents to memory. The WITH keyword will flush and close the file for us
        with open("messagingPartner.json", "r") as f:
            contents = f.read()

        # Convert the contents of the file into JSON format
        reciever = json.loads(contents)

        # Set the global onion routing variables so it knows the reciever we would like to create a circuit to
        Networking.OR.recieverIP = reciever['ip']
        Networking.OR.recieverPort = reciever['port']


    def router(self, data):
        logging.info("SEND TEXT START BEFORE DECRYPTON  START")

        reencoded = ast.literal_eval(data)
        peeledLayer = None
        # self.circuits = json.loads(self.circuits)
        # Loop through all the onion circuits that this node is a part of
        for circuit in circuits:
            # Attempt to decrypt the incoming data with each of our stored AES keys
            try:
                key = Fernet(circuit['key'])
                logging.debug("ATTMEPTING TO DECODE WITH ONION KEY" + str(key))
                peeledLayer = loads(key.decrypt(reencoded))
                # Delete the onion circuit after decryption. Each onion circuit is only used once for security!
                circuits.remove(circuit)
                # If decryption is successful then we no longer need to continue the loop
                break
            # Print out an error if key is wrong
            except:
                logging.error("Wrong key. CANNOT DECODE WITH KEY FROM OUR ONION CIRCUIT")



        logging.info("Incoming decoded data" + str(peeledLayer))

        # If after decoding the message the CMD is equal to forward then it means that we are an OR node and not the destination. Forward this onto the next hop
        if (peeledLayer['cmd'] == 'FWD'):
            logging.info("Fowarding Message")
            peeledLayerToSend = bytes(str(peeledLayer['msg']), 'utf-8')
            reactor.connectTCP(peeledLayer['ip'], int(peeledLayer['port']),
                               MessageFactory(peeledLayerToSend))
            self.debuggingWindow.info(peeledLayer)
            self.debuggingWindow.info("Fowarding message to the next OR!")
            logging.info("Fowarding message to the next OR")

        # If after decoding the message the CMD is equal to MSG then the contents are inteded for us! Use the messageRecieved method to display this in plaintext in the UI

        elif (peeledLayer['cmd'] == 'MSG'):
            logging.info("Recieving Message")
            self.messageRecieved(peeledLayer['msg'])
            logging.info("SEND TEXT AFTER DECRYPTION END")




        else:
            logging.error("Should never end up here")

    # Recieve an AES key for onion circuit
    def recieveORKey(self, data, transport):
        logging.info("Receiving a key for onion routing")
        logging.info(data)

        # Load in our private RSA key so we can decrypt the symmetric AES key
        with open("User.json", "r") as f:
            contents = f.read()
        currentUser = json.loads(contents)

        # Circuit dictionary is built from the incoming data
        circuit = {
            # "CIRCID": data['CIRCID'],
            "ip": transport,
            "key": self.asymmetricEncryption.decrypt(currentUser['publickey'], data['KEY']),
        }

        # Add the new circuit to the array
        circuits.append(circuit)
        logging.info(len(circuits))


    # Getters and Setters
    # Set the reciever of the onion messages port
    def setRecieverIP(self, recieverIP):
        self.recieverIP = recieverIP

    # Set the reciever of the onion messages port
    def setRecieverPort(self, recieverPort):
        self.recieverPort = recieverPort

    # Set the reciever of the onion messages publickey
    def setRecieverPublicKey(self, recieverPublicKey):
        self.recieverPublicKey = recieverPublicKey

    # Bread and butter of displaying incoming messages. Use a logger to write to the GUI window across threads. Replace the CMD bit also before displaying the original message to user
    def messageRecieved(self, data):
        self.debuggingWindow.info("Receiving a message")
        data = data.replace('==MSG==', '')
        # Writes message to the chat window using a global logger
        chatA = logging.getLogger("2")
        chatA.info(data)