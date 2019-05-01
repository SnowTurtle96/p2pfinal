'''
    File name: Utils.py
    Author: Jamie Clarke
    Date last modified: 18/03/2019
    Python Version: 3.7
'''
import hashlib
import json
import logging


class Utils:
    """

    Simple utility class that stores useful methods that can be applied throughout the application

    """
    # Generate ID method, will take a string and convert that into a sha256 and then return it
    def generateID(self, username):
        logging.info("This is what we are generating NODE ID from: " + str(username))
        hashed_file_value = hashlib.sha256(username.encode('utf-8')).hexdigest()
        logging.info("This is what we have generated as our NODE ID: " + str(hashed_file_value))
        return str(hashed_file_value)

    # Utility method to write the reciptient to the file system. Returns the data in JSON format once it has finished writing to file
    def writeRecipitent(self, data):
        file = open("messagingPartner.json", "w+")
        messagingPartnerInfo = json.dumps(data)
        file.write(messagingPartnerInfo)
        file.flush()
        file.close()
        return messagingPartnerInfo
