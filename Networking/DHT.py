'''
    File name: DHT.py
    Author: Jamie Clarke
    Date last modified: 18/03/2019
    Python Version: 3.7
'''

import json
import logging

from Models.FingerTable import FingerTable
from Networking.OR import OR
from Utils.Utils import Utils


class DHT():
    """

    DHT class maintains the nodes DHT and provides methods that can load this information along with the algoirthms for determining this nodes and new nodes positions

    Attributes:
        fingerTable -          Maintains this nodes ID along with network information for its successor and predecessor in the ring
    """

    # LoadDHTInformation reads in the DHT.json file to memory. It will then update the finger table with the credentials saved in the file.
    # Reading and writing to this file helps maintain state, this file is updated often
    # DHT.json is considered the source of truth for local routing information and current DHT position
    def loadDHTInformation(self):
        # Read in the contents of DHT.json and convert to JSON format
        with open ("DHT.json", "r") as f:
            contents = f.read()
        dhtfile = json.loads(contents)

        # update the finger table with the contents of DHT.json
        self.fingerTable.successor = dhtfile['successor']
        self.fingerTable.predecessor = dhtfile['predecessor']
        self.fingerTable.nodeid = dhtfile['nodeid']

    # Write the finger table stored in memory to file.
    def writeDHTInformation(self):
        # Open DHT.JSON for writing, dump the finger table object to a JSON string, write result to file
        with open("DHT.json", "w+") as f:
            dhtinfo = json.dumps((self.fingerTable.toDict()))
            f.write(dhtinfo)

    """
    updateSuccessor() & updatePredecessor()
    
    A collection of methods for updating attributes of the finger table
    Each method takes in the parameter data, this takes the form of a user object. 
    A new DHT is initialized and populated with the information in the DHT.json file. The update is applied to the attribute and this is then written back to file
    
    DHTPackageFromExternalNode()
    
    This method is invoked from the bootstrapping procedure and is only used when a node has no routing information at all. In this case it will get a complete copy
    of its routing table created by the external node it bootstraps from

    Arguments 
    data (user): Takes a user object

    """
    def updateSuccessor(self, data):
        dht = DHT()
        dht.loadDHTInformation()
        dht.fingerTable.successor = data
        dht.writeDHTInformation()

    def updatePredecessor(self, data):
        dht = DHT()
        dht.loadDHTInformation()
        dht.fingerTable.predecessor = data
        dht.writeDHTInformation()

        """
        DHTPackageFromExternalNode()

        This method is invoked from the bootstrapping procedure and is only used when a node has no routing information at all. In this case it will get a complete copy
        of its routing table created by the external node it bootstraps from

        Arguments 
        data (user): Takes a user object

        """

    def DHTPackageFromExternalNode(self, data):
        dht = DHT()
        dht.loadDHTInformation()
        dht.fingerTable.nodeid = data['nodeid']
        dht.fingerTable.successor = data['successor']
        dht.fingerTable.predecessor = data['predecessor']
        dht.writeDHTInformation()

        """
        DHTSearchReturn()

        This method is invoked when a response is recieved from the network with the messaging partner requested.
        This user is then saved to file so we can retain this information and not have to re-search
        
        Once a messaging partners routing information has been obtained an onion route is then created forming a circuit
        to this partner.

        Arguments 
        data (user): Takes a user object

        """

    def DHTSearchReturn(self, data):
        # Write the contact information of our user to a local file for use
        utils = Utils()
        messagingPartnerInfo = utils.writeRecipitent(data)
        messagingPartnerInfo = json.loads(messagingPartnerInfo)

        # Open file and write to it
        with open("DHT.json", "r") as f:
            contents = f.read()
        self.recipitent = json.loads(contents)


        logging.info("ONION ROUTING START")

        # Instantiate our onion router
        onionRouter = OR()

        # Set the end node (reciever)
        OR.recieverIP = messagingPartnerInfo['ip']
        OR.recieverPort = int(messagingPartnerInfo['port'])
        OR.recieverPublicKey = messagingPartnerInfo['publickey']

        # Create our circuit
        onionRouter.constructRoute(self.recipitent)
        onionRouter.createOnionKeys()
        OR.loadInRecipitent()
        onionRouter.exchangeKeys()

        logging.info("ONION ROUTING END")



    def __init__(self):
        self.fingerTable = FingerTable()
