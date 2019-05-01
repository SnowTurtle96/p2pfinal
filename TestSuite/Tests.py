import os
from pathlib import Path

import Networking
from Client import Client
from Encryption.AsymmetricEncryption import AsymmetricEncryption
from Encryption.SymmetricEncryption import SymmetricEncryption
from Models.User import User
import json
from unittest import TestCase

from Networking.OR import OR
from Networking.DHT import DHT
from Utils.StateChecks import checkDHTInitialized, checkSessionExists
from Utils.Utils import Utils


class TestDHT(TestCase):
    dht = DHT()
    dht1 = DHT()

    dht.fingerTable.predecessor = "Alice"
    dht.fingerTable.successor = "Bob"
    dht.fingerTable.nodeid = "Trudy"
    def test_loadDHTInformation(self):


        self.dht.writeDHTInformation()
        self.dht1.loadDHTInformation()
        self.assertTrue(self.dht1.fingerTable.nodeid == "Trudy")

    def test_writeDHTInformation(self):
        self.dht.writeDHTInformation()
        file = Path("DHT.json")
        self.assertTrue(file.is_file())

    def test_updateSuccessor(self):
        self.dht.writeDHTInformation()
        self.dht.loadDHTInformation()
        self.dht.updatePredecessor("Bob")
        self.dht.loadDHTInformation()
        self.assertTrue(self.dht.fingerTable.predecessor == "Bob")
    def test_updatePredecessor(self):
        self.dht.writeDHTInformation()
        self.dht.loadDHTInformation()
        self.dht.updateSuccessor("Alice")
        self.dht.loadDHTInformation()
        self.assertTrue(self.dht.fingerTable.successor == "Alice")




class TestAsymmetricEncryption(TestCase):
    dht = DHT()

    def setUp(self):
        self.asymmetricEncryption = AsymmetricEncryption()
        self.symmetricEncryption = SymmetricEncryption()

        self.onionrouter = OR()
        self.peers = open("../DHT.json", "r")
        self.peers = self.peers.read()
        self.peers = json.loads(self.peers)

    # Ensure that a public and private key pair are generated
    def test_generate_keys(self):
        self.asymmetricEncryption.generate_keys()
        self.assertTrue(self.asymmetricEncryption.private_key != None and self.asymmetricEncryption.public_key != None)

    # Simple test to ensure that the generated private key is saved to the local file server. Its important that this key is not lost.
    def test_save_key(self):
        self.asymmetricEncryption.generate_keys()
        self.asymmetricEncryption.save_key(self.asymmetricEncryption.private_key, 'privatekey')
        privatekeyfile = Path("privatekey")
        self.assertTrue(privatekeyfile.is_file())

    # Test that encryption method works. Plain text is entered and checked against the cipher text
    def test_encrypt(self):
        self.asymmetricEncryption.generate_keys()
        plaintext = "plaintext"
        plaintext = plaintext.encode('utf-8')
        ciphertext = self.asymmetricEncryption.encrypt(self.asymmetricEncryption.getPublicKey().decode("utf-8"), plaintext)
        self.assertTrue(plaintext != ciphertext)

    def test_decrypt(self):
        self.asymmetricEncryption.generate_keys()
        initialText = "plaintext"
        encoded = initialText.encode('utf-8')
        ciphertext = self.asymmetricEncryption.encrypt(self.asymmetricEncryption.getPublicKey().decode("utf-8"), encoded)
        plaintextDecrypted = self.asymmetricEncryption.decrypt("2",ciphertext)
        plaintextDecrypted = plaintextDecrypted.decode('utf-8')

        self.assertTrue(initialText == plaintextDecrypted)


# Test the utility class
class TestUtils(TestCase):
    def setUp(self):
        self.utils = Utils()

    def test_generateID(self):
        result = self.utils.generateID("Alice")
        self.assertTrue(result == '3bc51062973c458d5a6f2d8d64a023246354ad7e064b1e4e009ec8a0699a3043')

    def test_writeRecipitent(self):
        recipitent = {"ip": "localhost", "port": "8000", "user": "Bob",
                      "nodeid": "cd9fb1e148ccd8442e5aa74904cc73bf6fb54d1d54d333bd596aa9bb4bb4e961",
                      "publickey": "-----BEGIN PUBLIC KEY-----\n"}
        self.utils.writeRecipitent(recipitent)
        my_file = Path("messagingPartner.json")
        if (my_file.is_file()):
            self.assertTrue(True)
        else:
            self.assertTrue(False)


# Test that a key is generated and they are all unique
class TestSymmetricEncryption(TestCase):
    def setUp(self):
        self.symmetricEncryption = SymmetricEncryption()
    def test_createKeys(self):
        key1 = self.symmetricEncryption.createKeys()
        key2 = self.symmetricEncryption.createKeys()
        key3 = self.symmetricEncryption.createKeys()
        self.assertTrue(key1 != key2 != key3)

