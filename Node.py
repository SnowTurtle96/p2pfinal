from __future__ import print_function

from twisted.internet import reactor, protocol

from Client import Client
from Server.Server import Server

'''
    File name: Node.py
    Author: Jamie Clarke
    Date last modified: 04/04/2019
    Python Version: 3.7
'''

def main():
    """Main method creates two processes that run on the event loop,
     the server and the client"""
    factory = protocol.ServerFactory()
    factory.protocol = Server
    # Listen on port 10000 over TCP
    reactor.listenTCP(8000, factory)
    reactor.callLater(0, Client.Client)
    reactor.run()


if __name__ == '__main__':
    main()
