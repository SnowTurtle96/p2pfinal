'''
    File name: Route.py
    Author: Jamie Clarke
    Date last modified: 18/03/2019
    Python Version: 3.7
'''


class Route():
    """
       Route class is a simple model that stores routing information for the created path through the network

       Attributes:
           hop1 -          Stores the first hop of the onion route
           hop2 -          Stores the second hop of the onion route

       """
    hop1 = ''
    hop2 = ''

    # Convert this object into type dictionary. Each attribute is assigned to key/value pairs
    def toDict(self):
        return {"hop1": self.hop1, "hop2": self.hop2}
