'''
    File name: Client.py
    Author: Jamie Clarke
    Date last modified: 25/03/2019
    Python Version: 3.7
'''

import hashlib
import json
import logging
import os
from tkinter import *
from tkinter import scrolledtext

from twisted.internet import reactor, protocol, tksupport

import Networking
from Client.DHTRegistration import DHTRegistration
from Client.DHTSearch import DHTSearch
from Client.MessageFactory import MessageFactory
from Encryption.AsymmetricEncryption import AsymmetricEncryption
from Models.User import User
from Networking.DHT import DHT
from Networking.OR import OR
from Utils import StateChecks, Globals, Utils

# Instanitate a useful logger. The handler also allows us to log information to file which will appear in client.log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.FileHandler("{0}/{1}.log".format("./", "client")),
        logging.StreamHandler()
    ])
logger = logging.getLogger()


class Client(protocol.Protocol, logging.Handler):
    """

    Client class handles displaying the user interface and managing user input depending on system state.

    Attributes:
        peers -          Stores our DHT information
        networkDataExists -   Tracks if we have joined a p2p network or not
        user -           Tracks the current users informaton
        nodeid -         GUI text area that displays our nodeid
        predecessor -    GUI text area that displays our predecessor
        successor -      GUI text area that displays our successor
        stateOfRecipient - GUI text area that displays when the searched recipitent has been found in the DHT and is available for messaging
        messageEntry -   GUI element that takes a users written message

    """
    # Tracks if we have joined a network or not
    networkDataExists = True;
    # Is used to store loaded in DHT information
    peers = None
    # Stores our user file
    user = None
    # These needs to be a global so that we can activate it and deactivate it based on DHT recipient status
    nodeID = None
    predecessor = None
    successor = None
    messageEntry = None
    # GUI text box that indicates to the user when the searched recipitent has been found in the DHT and is available for messaging
    stateOfRecipient = None

    # Instantiate a local copy of asymmetric encryption
    encryption = AsymmetricEncryption()
    # Instantiate a local copy of the utility class allowing us to use useful functions
    Utils = Utils.Utils()

    # Initialization method for the client class
    # Determine whether or not this node is already a member of a network. Launch the correct UI depending on the result

    def __init__(self):
        self.networkDataExists = StateChecks.checkDHTInitialized()
        if (self.networkDataExists):
            # If network data exists then we will read our DHT data into memory
            logging.info("Network data loaded, booting main GUI")

            with open("DHT.json", "r") as f:
                contents = f.read()
            self.peers = json.loads(contents)

            # Load our user credentials into memory, this is used by a number of methods
            with open("User.json", "r") as f:
                contents = f.read()
            self.user = json.loads(contents)
            self.mainGUI()

        # If network data does not exist on the local disk then we will enter first time setup
        elif (self.networkDataExists == False):
            logging.info("No network data, launching initital UI")
            self.initialGUI()

        # Attempt to remove the previous messaging partner on application startup. If one does not exist exception is thrown and application continues to boot
        try:
            os.remove("messagingPartner.json")
        except:
            logging.debug("No previous partner!")

        logging.info("Client has been initialized!")

    # This method contains all the tkinter logic for displaying the initial UI.
    def initialGUI(self):
        # Initialing tkinter creates the root window and the tkinter interpreter
        root = Tk()
        # This installs the tkinter object into the twisted event loop. It will no longer hijack the main loop.
        tksupport.install(root)
        # Set the size of the tkinter window, we only need a small work space for the initial UI
        root.geometry("300x300+200+200")
        root.title('Initial Setup')
        root.geometry('{}x{}'.format(460, 350))

        leftFrame = Frame(root)
        leftFrame.pack(side="left", expand=True, fill="both")

        # Create a frame to be added to the window, this will be the right hand side of the UI
        rightFrame = Frame(root)
        rightFrame.pack(side="right", expand=True, fill="both")

        # Create a frame to be added to the window, this will be the left hand side of the UI
        leftFrame = Frame(root)
        leftFrame.pack(side="left", expand=True, fill="both")

        # This form is used for joining an exisiting network
        # Begin populating left frame with Labels and Entrys to take form data, uses tkinter grid method for positioning
        Label(leftFrame, text="Bootstrapping IP").grid(row=0, column=2, sticky=W)
        initialIP = Entry(leftFrame, width=19)
        initialIP.grid(row=1, column=2, sticky=W)

        Label(leftFrame, text="Boostrapping Port").grid(row=2, column=2, sticky=W)
        initialPort = Entry(leftFrame, width=19)
        initialPort.grid(row=3, column=2, sticky=W)

        Label(leftFrame, text="Your IP").grid(row=4, column=2, sticky=W)
        yourIP = Entry(leftFrame, width=19)
        yourIP.grid(row=5, column=2, sticky=W)

        Label(leftFrame, text="Your Port").grid(row=6, column=2, sticky=W)
        yourPort = Entry(leftFrame, width=19)
        yourPort.grid(row=7, column=2, sticky=W)

        Label(leftFrame, text="Username").grid(row=8, column=2, sticky=W)
        userName = Entry(leftFrame, width=19)
        userName.grid(row=9, column=2, sticky=W)

        # This form is used for starting a new network
        # Begin populating left frame with Labels and Entrys to take form data, uses tkinter grid method for positioning
        Label(rightFrame, text="Username").grid(row=8, column=2, sticky=W)
        username = Entry(rightFrame, width=19)
        username.grid(row=9, column=2, sticky=W)

        Label(rightFrame, text="Your IP").grid(row=10, column=2, sticky=W)
        yourip = Entry(rightFrame, width=19)
        yourip.grid(row=11, column=2, sticky=W)

        Label(rightFrame, text="Your Port").grid(row=12, column=2, sticky=W)
        yourport = Entry(rightFrame, width=19)
        yourport.grid(row=13, column=2, sticky=W)

        Button(leftFrame, text='Connect to existing',
               command=lambda arg1=initialIP, arg2=initialPort, arg3=yourIP, arg4=yourPort,
                              arg5=userName: self.connectToExistingNetwork(arg1, arg2, arg3, arg4,
                                                                           arg5)).grid(
            row=14, column=2, sticky=W)

        Button(rightFrame, text='Start a network',
               command=lambda arg1=yourip, arg2=yourport, arg3=username: self.createNewNetwork(yourip, yourport,
                                                                                               username)).grid(row=15,
                                                                                                               column=2,
                                                                                                               sticky=W)

    # Contains all the tkinter logic for displaying the main UI.
    def mainGUI(self):
        # Declare these variables as global so it is clear to the reader these are used elsewhere
        # These variables need to be global so they can be accessed within updateGUI
        global root
        global predecessor
        global successor
        global nodeID
        global stateOfRecipient
        global messageEntry

        # Useful log information to keep track of application state
        logger.info("Main UI Launched")

        # Initialize tkinters main window
        root = Tk()
        # This installs the tkinter object into the twisted event loop. It will no longer hijack the main loop.
        tksupport.install(root)
        # Sets the current username to the title of the application window
        root.title(self.peers['nodeid']['user'])

        # Sets the logo of the application to a lock icon
        root.iconbitmap('@logo.xbm')

        # Creates tkinter string variables which allows info on the ui to be changed dynamically
        # Set the default text of these string vars

        currentPeer = StringVar()
        currentPeer.set("Select a peer to message")

        recipitentIP = StringVar()
        recipitentIP.set("NULL")

        recipitentPORT = StringVar()
        recipitentPORT.set(10000)

        stateOfRecipient = StringVar()
        stateOfRecipient.set("CIRCUIT NOT CREATED")

        messageToSend = StringVar()
        messageToSend.set("Type here to send a message...")

        userToSearch = StringVar()
        userToSearch.set("Search the DHT for a user")

        # Initialize stringvars
        nodeID = StringVar()
        nodeID.set("DHT not intialized!")

        predecessor = StringVar()
        predecessor.set("DHT not initialized!")

        successor = StringVar()
        successor.set("DHT not initialized!")

        # Creation of frame for the left hand side of the UI
        menu_left = Frame(root, width=10, height=50)
        # Split the left side into upper and lower frames, then add these to the left hand side frame
        menu_left_upper = Frame(menu_left, width=10, height=50)
        menu_left_lower = Frame(menu_left, width=10, height=50)

        # Apply a grid layout to left upper and left lower frames
        menu_left_upper.grid(row=1, column=0, sticky=W)
        menu_left_lower.grid(row=1, column=1, sticky=W)

        # right area
        statusBarRight = Frame(root, bg="#dfdfdf")

        currentPeer = Label(statusBarRight, textvariable=currentPeer, bg="#dfdfdf", borderwidth=2,
                                  relief="groove")

        currentPeer.grid(row=2, column=1)

        chat_textbox = scrolledtext.ScrolledText(root, width=70, height=30, borderwidth=2, relief="groove")
        chat_textbox.grid(row=1, column=1)

        # Create logging window
        logging2 = scrolledtext.ScrolledText(menu_left_lower, width=50, height=30, borderwidth=2, relief="groove")
        logging2.grid(row=2, column=0)
        logging2.configure(font='TkFixedFont')

        # Create logging handlers
        # Debug handler displays useful information about the application to the user on the right hand side of the UI
        debug_handler = DebugHandler(logging2)
        # Chat handler is used to write incoming messages to the scrolling chat window on the left hand side of the UI
        chat_handler = ChatHandler(chat_textbox)

        # Logging configuration
        logging.basicConfig(filename='test.log',
                            level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        """Add hander to the logger"""
        userInfo = logging.getLogger("1")
        userInfo.addHandler(debug_handler)

        userInfo.info("Started Application")

        """Add hander to the logger"""
        chatA = logging.getLogger("2")
        chatA.addHandler(chat_handler)

        # status bar
        status_frame = Frame(root, height=10)

        # Displays current application version

        version = Label(menu_left_lower, text="Version: 1.0.0", width="20", borderwidth=2, relief="groove").grid(row=0,
                                                                                                                 column=0,
                                                                                                                 sticky=W)
        # Displays the author of the application
        author = Label(menu_left_lower, text="Author: Jamie Clarke", width="20", borderwidth=2, relief="groove").grid(
            row=0, column=1, sticky=EW)

        # Button pressed send a search query to the network
        DHTSearchButton = Button(menu_left_lower, width="10", text='Search!',
                                command=lambda arg1=userToSearch: self.searchDHT(arg1)).grid(row=1, column=1, sticky=W)

        # A text entry that contains the user to be searched for
        search_user = Entry(menu_left_lower, textvariable=userToSearch, width="80").grid(row=1, column=0, sticky=W)
        messageToSend.set("Type here to send a message...")

        # A text entry where the user can write a message to send another user
        messageEntry = Entry(status_frame, textvariable=messageToSend, width="80")
        messageEntry.grid(row=6, column=0, sticky=W)

        Button(status_frame, text='Send',
               command=lambda arg1=messageToSend: self.sendMsg(arg1)).grid(
            row=6, column=1, sticky=EW)

        # Add labels to the right status bar
        nodeidLabel = Label(statusBarRight, textvariable=nodeID, width=35, borderwidth=2, relief="groove").grid(row=1,
                                                                                                                  column=0,
                                                                                                                  sticky=W)
        predecessorLabel = Label(statusBarRight, textvariable=predecessor, width=35, borderwidth=2,
                                 relief="groove").grid(row=1, column=1, sticky=EW)
        successorLabel = Label(statusBarRight, textvariable=successor, width=35, borderwidth=2, relief="groove").grid(
            row=1, column=2)
        statusLabel = Label(statusBarRight, textvariable=stateOfRecipient, width=35, borderwidth=2,
                            relief="groove").grid(
            row=1, column=3, sticky=W)

        # Set the grid type of the UI frames
        menu_left.grid(row=0, column=10, rowspan=2, sticky="nsew")
        statusBarRight.grid(row=0, column=1, sticky="ew")
        status_frame.grid(row=2, column=0, columnspan=2, rowspan=4, sticky="ew")

        # Configure the weights of the grid formation
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(1, weight=1)

        # Disable the message entry field by default. Prevent message sending without a recipitent or onion route
        messageEntry.config(state=DISABLED)

        # Begin the recursive method of updating our UI
        self.updateGUI()

    """
    
    This method is called from a button listener within the main UI tkinter interface
    it will take a single username parameter, find its SHA256 hash and then send the request
    to its successor using the search protocol
    
    Arguments 
    username (string): Takes a username which will searched for within the network
    
    """
    def searchDHT(self, username):
        # Convert the username into a hash value that we can use to search the network
        usernameHash = hashlib.sha256(username.get().encode('utf-8')).hexdigest()

        DHTUserRequest = {}
        DHTUserRequest['username'] = usernameHash
        DHTUserRequest['ip'] = self.peers['nodeid']['ip']
        DHTUserRequest['port'] = self.peers['nodeid']['port']

        reactor.connectTCP(self.peers['successor']['ip'], int(self.peers['successor']['port']),
                           DHTSearch(DHTUserRequest))

        logging.info("SEARCH START")

    """

    updateGUI is a method that fires every 2s. Using global variables it accesses tkinter UI componetns and updates them with fresh data being recieved by the server module
    This method is also responsble for form validation. It will enable and disable UI components depending on the applications state
    Firing every two seconds is handled by calling itself at the end of each update with root.after.

    """

    def updateGUI(self):
        global nodeID
        global predecessor
        global successor
        global stateOfRecipient
        global messageEntry

        with open("DHT.json", "r") as f:
            contents = f.read()
        self.peers = json.loads(contents)

        predecessorstr = self.peers['predecessor']['user']
        successorstr = self.peers['successor']['user']
        nodeidstr = self.peers['nodeid']['nodeid']

        predecessor.set("Predecessor: " + predecessorstr)
        successor.set("Successor: " + successorstr)
        nodeID.set("Node ID: " + nodeidstr)

        sessionCreated = StateChecks.checkSessionExists()

        if (sessionCreated == True):
            stateOfRecipient.set("CIRCUIT CREATED!")
            messageEntry.config(state=NORMAL)

        root.after(2000, self.updateGUI)

    """

    Create a network is called by an event listener within the main ui interface. This method will take three parameters 
    required for starting a new network from the tkinter interface and parse them.
    
    A DHT object will be initalized to provide a base routing table.
    The applications asymmetric encryption keys will be generated
    The parsed user details will be added to a user object, this user object is then saved to the local file system
    The user object is then set as our node in the local routing table so it can be shared if new nodes join
    
    Arguments 
    localip (string): Takes the ip address of the users machine
    localport (string): Takes the port that the application will be reachable on
    username (string): Takes the pseudonym that the user wishes to be known by
    
    """

    def createNewNetwork(self, localip, localport, username):
        logging.info("Creating a new network")
        localip = str(localip.get())
        localport = str(localport.get())
        username = str(username.get())
        localport = str(localport)

        """Initialize DHT"""
        initialization = DHT()

        self.encryption.generate_keys()

        # Create a user object, set all user variables to the data gathered in the form
        user = User()
        user.ip = localip
        user.port = localport
        user.username = username
        user.publicKey = self.encryption.getPublicKey().decode("utf-8")
        user.nodeid = self.Utils.generateID(user.username)

        # Convert our user to json format so we can save it to file
        userAsJSON = json.dumps(user.toDict())
        # Register username in a local file so we know who we are
        file = open("User.json", "w+")
        file.write(str(userAsJSON))
        file.close()

        initialization = DHT()
        initialization.fingerTable.nodeid = user.toDict()
        initialization.writeDHTInformation()

    """

    This method is called by an event listener in the initial UI. The method takes several paramaters about the local and remote node
    Tkinter variables will be taken and parsed into regular primitives. Asymmetric keys will be generated and the request to join the network
    to the specified bootstrapping node will be sent using the Registration Factory.
    
    Arguments 
    bootstrapIP (string): Takes the ip address of a node in the network the user wishes to join
    bootstrapPort (int): Takes the port that the node in the network can be reached on over TCP
    localIP (string): Takes the local users ip address
    localPort (int): Takes the local users port the application can be reached on
    username (string): Takes the pseudonym that the user wishes to be known by

    """

    def connectToExistingNetwork(self, bootstrapIP, bootstrapPort, localIP, localPort, username):
        global listbox
        bootstrapIP = str(bootstrapIP.get())
        bootstrapPort = str(bootstrapPort.get())
        localIP = str(localIP.get())
        localPort = str(localPort.get())
        username = str(username.get())
        """
        General data sanitation from the UI into things that our twisted application can understand
        Encoding as bytes for transfer
        """
        bootstrapPort = int(bootstrapPort)

        """Create our encryption keys"""
        self.encryption.generate_keys()
        logger.info("public key")
        logger.info(self.encryption.public_key)
        logger.info("Encryption public key")
        logger.info(self.encryption.getPublicKey())
        logger.info("Encryption private key")
        logger.info(self.encryption.getPrivateKey())

        """Initialize DHT"""
        initialization = DHT()

        user = User()
        user.ip = localIP
        user.port = localPort
        user.username = username
        user.publicKey = self.encryption.getPublicKey().decode("utf-8")
        user.nodeid = self.Utils.generateID(user.username)
        initialization.fingerTable.nodeid = user.toDict()
        initialization.writeDHTInformation()

        user.publicKey = self.encryption.getPublicKey().decode("utf-8")
        """Register username in a local file so we know who we are"""
        file = open("User.json", "w+")
        userstr = json.dumps(user.toDict())
        file.write(str(userstr))
        logger.info("Models Dict" + userstr)

        logging.info("BOOTSTRAP TIME START")

        reactor.connectTCP(bootstrapIP, bootstrapPort, DHTRegistration(userstr))

    """

    This method is called by an event listener in the main UI. It will takes the ip port of the destination node as well as a message in plaintext.
    A route is created by the onion routing module and encryption will be applied to the message
    The result will be returned from the onion routing module and then sent to the first hop of the circuit using connectTCP    

    Arguments 
    ip (string): Takes the ip address of a node in the network the user wishes to join
    port (int): Takes the port that the node in the network can be reached on over TCP
    msg (string): Takes the local users ip address

    """

    def sendMsg(self, msg):
        msgCMD = "==MSG=="

        logging.info("SEND TEXT START BEFORE ONION ROUTING")

        # Open and read from the file messagingPartner, this will read in the credentials of your messaging partner
        with open("messagingPartner.json", "r") as f:
            contents = f.read()
        self.recipitent = json.loads(contents)

        """Assign protocol command"""
        msg = msgCMD + self.getCurrentUser().upper() + ":" + " " + msg.get()
        OR.loadInRecipitent()
        OR.encryptMsgForOnionRouting(msg)

        onionMessage = OR.encryptedMessage
        logging.info("Sending Message" + str(onionMessage))
        onionMessage = str(onionMessage)
        onionMessage = bytes(onionMessage, 'utf-8')
        logging.info("SEND TEXT START AFTER ONION ROUTING")

        # Use the reactor to establish TCP connection to the first hop of the route
        reactor.connectTCP(Networking.OR.route.hop1['ip'], int(Networking.OR.route.hop1['port']),
                           MessageFactory(onionMessage))


        Globals.circuitTracker = 0
        Globals.circuitEstablished = False

        sanitisedData = msg.replace('==MSG==', '')
        chatA = logging.getLogger("2")
        chatA.info(sanitisedData)
        print(onionMessage.decode('utf-8'))

    # Getter method for the current user
    def getCurrentUser(self):
        return self.user['user']


# Interesting methods that allow us to perform global logging to tkinters text area
# Allows logging across many threads
class DebugHandler(logging.Handler):

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state='normal')
            self.text.insert(END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(END)

        self.text.after(0, append)


# Interesting methods that allow us to perform global logging to tkinters text area
# Allows logging across many threads
class ChatHandler(logging.Handler):

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state='normal')
            self.text.insert(END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(END)

        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)
