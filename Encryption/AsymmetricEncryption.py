'''
    File name: AsymmetricEncryption.py
    Author: Jamie Clarke
    Date last modified: 21/04/2019
    Python Version: 3.7
'''

import logging

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key


class AsymmetricEncryption:
    """

    Asymmetric encryption handles the generation of keys as well as the encryption and decryption of RSA messages

    Attributes:
        private_key -   Stores RSA 4096-bit private key
        public_key -   Stores RSA 4096-bit public key

    """

    private_key = None
    public_key = None

    # Generates a pair of RSA keys with a size of 4096bits. Generates the private key and then the matching public key. Both are then saved

    def generate_keys(self):
        logging.info("Generating our asymmetric public and private key")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend())

        self.public_key = private_key.public_key()
        self.private_key = private_key
        self.save_key(private_key, "privatekey")

    # Getter method for the private key
    def getPrivateKey(self):
        logging.info("Retrieving our asymmetric private key")
        return self.private_key

    # Getter method for the public key
    def getPublicKey(self):
        logging.info("Retreiving our asymmetric public key")
        pem_public_key = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)

        with open("publickey", 'wb') as pem_out:
            pem_out.write(pem_public_key)

        return pem_public_key

    """
    
     Save key takes two parameters, a key and the desired file name to save the key under
     Method converts the key into a bytes representation using PEM encoding. A file is then
     created using the filename provided by. Key is then written out to the file

      :param key (bytes):       Takes a RSA key 
      :param filename (string): Takes a string representing the desired filename
      
    """

    def save_key(self, key, filename):
        logging.info("Saving our public/private key to file")
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        with open(filename, 'wb') as pem_out:
            pem_out.write(pem)

    """

     Encrypt takes a key and a plaintext message. It will then apply the key to the message resulting in a encrypted ciphertext message

      :param key (bytes):       Takes a RSA key 
      :param message (string):  Takes a string representing a plain text message
      :return ciphertext:       Returns a message encrypted with 4096bit RSA

    """

    def encrypt(self, key, message):
        logging.info("Encrypting a message with asymmetric key")
        key = key.encode("utf-8")

        public_key = load_pem_public_key(key, default_backend())

        ciphertext = public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None))
        return ciphertext

    """

     Decrypt takes a key and a bytes representation of a ciphertext message. It will then apply the key to the message 
     resulting in a decrypted plaintext message

      :param key (bytes):       Takes a RSA key 
      :param message (bytes):   Takes a bytes representation of RSA cipher text
      :return message (string):       Returns a plaintext decrypted string

    """

    def decrypt(self, key, message):
        logging.info("Decrypting a message with asymmetric key")
        with open("privatekey", "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend())
        message = private_key.decrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None
            )
        )

        return message
