from typing import List
class Address(dict):
    def __init__(self, ip: str, port: int):
        dict.__init__(self, ip=ip, port=port)
        self.ip   = ip
        self.port = port
                          
    def __str__(self):
        return f"{self.ip}:{self.port}"
    
    def __iter__(self):
        return iter((self.ip, self.port))
    
    def __hash__(self):
        return hash((self.ip, self.port))
    
    def __eq__(self, other):
        return self['ip'] == other['ip'] and self['port'] == other['port']
    
    def __ne__(self, other):
        return not self.__eq__(other)