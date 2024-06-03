from typing import List
class Address(dict):
    # create static list of addresses
    addresses = []
    def __init__(self, ip: str, port: int):
        dict.__init__(self, ip=ip, port=port)
        self.ip   = ip
        self.port = port
        # if self not in Address.addresses:
        Address.addresses.append(self)
                
    def __str__(self):
        return f"{self.ip}:{self.port}"
    
    def __iter__(self):
        return iter((self.ip, self.port))
    
    def __eq__(self, other):
        return self.ip == other.ip and self.port == other.port
    
    def __ne__(self, other):
        return self.ip != other.ip or self.port != other.port