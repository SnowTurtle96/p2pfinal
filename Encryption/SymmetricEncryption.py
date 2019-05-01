from cryptography.fernet import Fernet


class SymmetricEncryption():
    """
     Symmetric encryption handles the generation of keys as well as the encryption and decryption of AES messages

    """

    """

     Simple method that uses an external library to generate an AES 128bit key. This is then returned

      :return key (bytes): Returns an AES 128bit in bytes format

    """
    def createKeys(self):
        # A incredibly simple method provided by fernet. Generates a symmetric aes key that is 128bits long
        key = Fernet.generate_key()
        return key
