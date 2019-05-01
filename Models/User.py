'''
    File name: User.py
    Author: Jamie Clarke
    Date last modified: 18/03/2019
    Python Version: 3.7
'''


class User():
    """

    User class maintains information about the user and is also used by other nodes to contact eachother

    Attributes:
        ip -          Stores the IP that this computer is operating on
        port -        Stores the port that the user has selected to open for listening by the server class
        user -        Stores our username
        publickey -   Stores our public key which will be used by other nodes for sending us encrypted symmetric keys
        nodeid -      Stores a SHA256 hash of our nodeid generated from our username

    """

    ip = ''
    port = ''
    username = ''
    publicKey = ''
    nodeid = ''

    # Stringify this object. Convert the object into a string
    def __str__(self):
        return (self.ip + self.port + self.username + self.publicKey + self.nodeid)

    # Convert this object into type dictionary. Each attribute is assigned to key/value pairs
    def toDict(self):
        return {"ip": self.ip, "port": self.port, "user": self.username, "nodeid": self.nodeid, "publickey": self.publicKey}

