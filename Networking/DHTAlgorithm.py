import ast
import json
import logging

from twisted.internet import reactor

from Client.DHTRegistration import DHTRegistration
from Client.DHTSearch import DHTSearch
from Networking.DHT import DHT
from Networking.DHTSearchReturn import DHTSearchReturn
from Server.DHTPredecessorUpdate import DHTPredecessorUpdate
from Server.DHTReturn import DHTReturn
from Server.DHTSuccessorUpdate import DHTSuccessorUpdate


class DHTAlgoirthm():
    dht = DHT()

    """
    DHTPositionSearch()

    DHTPositionSearch is the bread and butter of the DHT. This is brain behind the DHT
    Logic is outsourced to other methods
    Determines how the incoming node should be bootstrapped
    
    Arguments 
    incomingNode (user): Takes a user object

    """

    def DHTPositionSearch(self, incomingNode):
        logging.info("DHT position search ")

        # Remove the network command from the message
        incomingNode = incomingNode.replace('==REGISTER==', '')
        incomingNode = json.loads(incomingNode)

        # Read in the current users information
        with open("User.json", "r") as f:
            contents = f.read()
        currentUser = json.loads(contents)

        # Load the current DHT information from file
        self.dht.loadDHTInformation()
        logging.info("Loaded DHT information")

        # Determine how the bootstrapping request should be satisfied

        # Determines whether the node joining will be the second node
        if (self.dht.fingerTable.successor['nodeid'] == '' and self.dht.fingerTable.predecessor['nodeid'] == ''):
            logging.info("Second node has joined the DHT")

            self.secondNodeJoins(currentUser, incomingNode)

        # Determines whether the node joining will be the third node
        elif(self.dht.fingerTable.successor['nodeid'] == self.dht.fingerTable.predecessor['nodeid']):
            logging.info("Third node has joined the DHT")

            self.thirdNodeJoins(incomingNode)

        # Determines whether the local node resides at the first location of the DHT
        elif (self.dht.fingerTable.nodeid['nodeid'] < self.dht.fingerTable.predecessor['nodeid']):
            logging.info("Edge case start of DHT")

            self.startOfDHTEdgeCase(currentUser, incomingNode)


        # Determines whether the local node resides at the end of the DHT
        elif (self.dht.fingerTable.nodeid['nodeid'] > self.dht.fingerTable.successor['nodeid']):
            logging.info("Edge case end of DHT")
            self.endOfDHTEdgeCase(currentUser, incomingNode)

            """Check for edge case when we are at the start of our DHT"""

        # Determines whether the incoming node should be the local nodes predecessor
        elif (incomingNode['nodeid'] < self.dht.fingerTable.nodeid['nodeid'] and incomingNode['nodeid'] > self.dht.fingerTable.predecessor['nodeid']):
            logging.info("New predecessor no edge case")
            self.newPredecessor(incomingNode)

        # Determines whether the incoming node should be the local nodes successor
        elif (incomingNode['nodeid'] > self.dht.fingerTable.nodeid['nodeid'] and incomingNode['nodeid'] < self.dht.fingerTable.successor['nodeid']):
            logging.info("New successsor no edge case")
            self.newSuccessor(incomingNode)

        # Cannot satisfy this request, forwarded to the local nodes successor
        elif (incomingNode['nodeid'] > self.dht.fingerTable.successor['nodeid']):
            self.fowardRequestToSuccessor(incomingNode)

        # Cannot satisfy this request, forwarded to the local nodes predecessor
        elif (incomingNode['nodeid'] < self.dht.fingerTable.predecessor['nodeid']):
            self.fowardRequestToPredecessor(incomingNode)

        # Error - Possibly corrupted data in transit
        else:
            logging.error("Error should never reach this position")

    """
    thirdNodeJoins()

    thirdNodeJoins - Handles the edge case upon which 2 nodes are currently in the network and a third wishes to join. 

    Arguments 
    incomingNode (user): Takes a user object

    """

    def thirdNodeJoins(self, incomingNode):
        if(incomingNode['nodeid'] < self.dht.fingerTable.nodeid['nodeid']):
            """This handles the remote node"""
            self.newPredecessor(incomingNode)
        else:
            self.newSuccessor(incomingNode)

    """
    secondNodeJoins()

    secondNodeJoins - Handles the edge case where only 1 node is currently in the network and a second wishes to join
    The DHT must always form a circle, to achieve both nodes successor and predecessor point to each other. 

    Arguments 
    incomingNode (user): Takes a user object
    currentUser  (user): Takes the local nodes user details

    """

    def secondNodeJoins(self, currentUser, incomingNode):
        # Sets the local finger tables predecessor and successor to the new incoming node
        self.dht.fingerTable.predecessor = incomingNode
        self.dht.fingerTable.successor = incomingNode
        self.dht.fingerTable.nodeid = currentUser
        # Writes this updated DHT information to file
        self.dht.writeDHTInformation()

        # Send back the inverse of our finger table to the new node. E.g.the local node is the bootstrapping nodes successor and predecessor
        dhtForNewNode = DHT()
        dhtForNewNode.fingerTable.successor = currentUser
        dhtForNewNode.fingerTable.predecessor = currentUser
        dhtForNewNode.fingerTable.nodeid = incomingNode

        # Establish a TCP connection and return the calculated finger table
        reactor.connectTCP(incomingNode['ip'], int(incomingNode['port']),
                           DHTReturn(dhtForNewNode.fingerTable.toDict()))

    """
    startOfDHTEdgeCase()

    startOfDHTEdgeCase - Handles the edge case if the bootstrapping node is at the start of the ring, its predecessor is greater than itself. This requires a special bootstrap procedure

    Arguments 
    incomingNode (user): Takes a user object

    """

    def startOfDHTEdgeCase(self, incomingNode):
        logging.info("Edge case start of DHT")

        if (incomingNode['nodeid'] < self.dht.fingerTable.nodeid['nodeid'] and incomingNode['nodeid'] < self.dht.fingerTable.predecessor['nodeid']):
            self.newPredecessor(incomingNode)

        elif (incomingNode['nodeid'] > self.dht.fingerTable.nodeid['nodeid'] and incomingNode['nodeid'] < self.dht.fingerTable.successor['nodeid']):
            self.newSuccessor(incomingNode)

        elif (incomingNode['nodeid'] > self.dht.fingerTable.successor['nodeid']):
            self.fowardRequestToSuccessor(incomingNode)


        elif (incomingNode['nodeid'] < self.dht.fingerTable.predecessor['nodeid']):
            self.newSuccessor(incomingNode)

        else:
            logging.error("ERROR should never reach here")

    """
    endOfDHTEdgeCase()

    endOfDHTEdgeCase - Handles the edge case if the bootstrapping node is at the end of the ring, its successor is less than itself. This requires a special bootstrap procedure

    Arguments 
    incomingNode (user): Takes a user object

    """

    def endOfDHTEdgeCase(self, incomingNode):

        # Check that the incoming node is both greater than the local node id and greater than the local nodes successor
        if(incomingNode['nodeid'] > self.dht.fingerTable.nodeid['nodeid'] and incomingNode['nodeid'] > self.dht.fingerTable.successor['nodeid']):
            self.newSuccessor(incomingNode)

        # Check that the incoming node is both less than the local node id and greater than the local nodes successor
        elif (incomingNode['nodeid'] < self.dht.fingerTable.nodeid['nodeid'] and incomingNode['nodeid'] > self.dht.fingerTable.predecessor['nodeid']):
            self.newPredecessor(incomingNode)

        # Check that the incoming node is greater than the local nodes successor, if so the request cannot be satisied locally so is forwarded to the successor
        elif(incomingNode['nodeid'] > self.dht.fingerTable.successor['nodeid']):
            self.fowardRequestToSuccessor(incomingNode)

        # Check if the incoming node is less than the local nodes predecessor, if so this node now belongs at the start of the DHT and is the local nodes new successpr
        elif (incomingNode['nodeid'] < self.dht.fingerTable.predecessor['nodeid']):
            self.newSuccessor(incomingNode)

        else:
            logging.error("ERROR should never reach here")

    """
    newPredecessor(), newSuccessor(), fowardRequestTOPredecessor(), fowardRequestToSuccessor()

    The following methods represent standard DHT behaviour and will be the most commonly invoked. 
    
    newPredecessor - The incoming node is less than the local node ID and greater than the current predecessor
    newSuccessor -  The incoming node is greater than the local node ID and less than the current successor
    fowardRequestToPredecessor - The incoming node is less than the local predecessor
    fowardRequestToSuccessor - The incoming node is greater than the local successor
    
    Arguments 
    incomingNode (user): Takes a user object

    """

    def newPredecessor(self, incomingNode):

        """This handles the remote node"""
        dhtForNewNode = DHT()
        dhtForNewNode.fingerTable.successor = self.dht.fingerTable.nodeid
        dhtForNewNode.fingerTable.nodeid = incomingNode
        dhtForNewNode.fingerTable.predecessor = self.dht.fingerTable.predecessor

        # Stabilise the network by updating old predecessor with its new successor
        reactor.connectTCP(self.dht.fingerTable.predecessor['ip'],
                           int(self.dht.fingerTable.predecessor['port']), DHTSuccessorUpdate(incomingNode))

        # Provide the node being bootstrapped with network information allowing it to position itself in the network

        reactor.connectTCP(incomingNode['ip'], int(incomingNode['port']),
                           DHTReturn(dhtForNewNode.fingerTable.toDict()))

        # Update the local node with its new predecessor
        self.dht.fingerTable.predecessor = incomingNode
        # Write this new information to file
        self.dht.writeDHTInformation()

    def newSuccessor(self, incomingNode):

        # Create a finger table for the node being bootstrapped
        dhtForNewNode = DHT()
        dhtForNewNode.fingerTable.successor = self.dht.fingerTable.successor
        dhtForNewNode.fingerTable.nodeid = incomingNode
        dhtForNewNode.fingerTable.predecessor = self.dht.fingerTable.nodeid

        # Stabilise the network by updating old successor with its new predecessor

        reactor.connectTCP(self.dht.fingerTable.successor['ip'],
                           int(self.dht.fingerTable.successor['port']), DHTPredecessorUpdate(incomingNode))

        # Provide the node being bootstrapped with network information allowing it to position itself in the network

        reactor.connectTCP(incomingNode['ip'], int(incomingNode['port']),
                           DHTReturn(dhtForNewNode.fingerTable.toDict()))

        # Update the local node with its new successor
        self.dht.fingerTable.successor = incomingNode
        # Write this new information to file
        self.dht.writeDHTInformation()

    def fowardRequestToPredecessor(self, incomingNode):
        logging.info("DHT position request. Can't satisfy sending to the previous node")
        incomingNode = json.dumps(incomingNode)
        reactor.connectTCP(self.dht.fingerTable.predecessor['ip'],
                           int(self.dht.fingerTable.predecessor['port']), DHTRegistration(incomingNode))

    def fowardRequestToSuccessor(self, incomingNode):
        logging.info("DHT position request. Can't satisfy sending to the next node")
        incomingNode = json.dumps(incomingNode)
        reactor.connectTCP(self.dht.fingerTable.successor['ip'],
                           int(self.dht.fingerTable.successor['port']), DHTRegistration(incomingNode))

    """
    DHTInformationSearch
    
    This method encapsulates all the logic required to search the DHT for data
    Attempts to match a SHA256 value to those in its local stoage
    If the request can not be satisifed it will determine which direction the request
    should be fowarded in

    Arguments 
    userSearchRequest (dict): Takes a dict containing the return address of the search
    and a SHA256 encoding of a users pseudonym which is used in the search
    
    """

    def DHTInformationSearch(self, userSearchRequest):
        logging.info("DHT information search")

        # Remove the network command from the message
        userSearchRequest = userSearchRequest.replace("==DHTSEARCH==", "")
        self.dht.loadDHTInformation()
        # Convert the request into a dictionary object
        userSearchRequest = ast.literal_eval(userSearchRequest)

        logging.info("Incoming DHT Search Data" + str(userSearchRequest))

        # Check to see if the hash value is equivalent to our successors ID
        if (self.dht.fingerTable.successor['nodeid'] == userSearchRequest['username']):
            logging.info("Found user returning object successor")
            userfound = self.dht.fingerTable.successor
            reactor.connectTCP(userSearchRequest['ip'],
                               int(userSearchRequest['port']), DHTSearchReturn(userfound))

        # Check to see if the hash value is equivalent to our predecessors ID
        elif (self.dht.fingerTable.predecessor['nodeid'] == userSearchRequest['username']):
            logging.info("Found user returning object predecessor")
            userfound = self.dht.fingerTable.predecessor
            reactor.connectTCP(userSearchRequest['ip'],
                               int(userSearchRequest['port']), DHTSearchReturn(userfound))

        # Check to see if the hash value is equivalent to our own ID
        elif (self.dht.fingerTable.nodeid['nodeid'] == userSearchRequest['username']):
            logging.info("Found user is my NODEID!")
            userfound = self.dht.fingerTable.nodeid
            reactor.connectTCP(userSearchRequest['ip'],
                               int(userSearchRequest['port']), DHTSearchReturn(userfound))

        # Check if the hash value is greater than our ID, if so send to our successor
        elif (userSearchRequest['username'] > self.dht.fingerTable.nodeid['nodeid']):
            logging.info("Sending information request to our successor cannot satisfy request")
            reactor.connectTCP(self.dht.fingerTable.successor['ip'], int(self.dht.fingerTable.successor['port']),
                               DHTSearch(userSearchRequest))

        # Check if the hash value is greater than our ID, if so send to our successor
        elif (userSearchRequest['username'] < self.dht.fingerTable.nodeid['nodeid']):
            logging.info("Sending information request to our predecessor cannot satisfy request")
            reactor.connectTCP(self.dht.fingerTable.predecessor['ip'], int(self.dht.fingerTable.predecessor['port']),
                               DHTSearch(userSearchRequest))

        # Should not be possible to reach this position
        else:
            logging.error("ERROR! Should never reach this location")
