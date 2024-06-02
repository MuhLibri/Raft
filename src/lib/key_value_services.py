from struct.kvstore import KVStore
from struct.address import Address
import xmlrpc.client
from typing import Any, Optional

class KeyValueService:
    
    def __init__(self, 
                 store: dict = None,
                 server_addr: Optional[Address] = None,
                 server: Optional[xmlrpc.client.ServerProxy] = None,
                 max_retries: int = 3
                 ) -> None:
        
        if store:
            store = KVStore()
        self.store = store
            
        if server_addr:
            self.server_addr = server_addr
            self.server = xmlrpc.client.ServerProxy(f"http://{server_addr.ip}:{server_addr.port}")
        elif server:
            self.server = server
            self.server_addr = Address(server.server_addr[0], server.server_addr[1])
        else:
            raise ValueError("Either server_addr or server must be provided")
        
        self.max_retries = max_retries
    
    def __call_method(self, method: str, *params: Any) -> Any:
        retries = 0
        while retries < self.max_retries:
            try:
                func = getattr(self.server, method)
                return func(*params)
            except xmlrpc.client.Fault as fault:
                if fault.faultString.startswith("NOT_LEADER"):
                    # Move to private method
                    self._handle_leader_redirect(fault, retries)
                    retries += 1
                else:
                    print(f"Error calling method {method}: {fault.faultString}")
                    return None
            except AttributeError:
                print(f"Method {method} not found on server.")
                return None
            except Exception as e:
                print(f"Error calling method {method}: {e}")
                return None
        
        print(f"Maximum retries ({self.max_retries}) exceeded for method {method}.")
        return None
        
    def _handle_leader_redirect(self, fault: xmlrpc.client.Fault, retries: int) -> None:
        new_leader = fault.faultString.split()[1]
        ip, port = new_leader.split(':')
        self.server_addr = Address(ip, int(port))
        self.server = xmlrpc.client.ServerProxy(f"http://{self.server_addr.ip}:{self.server_addr.port}")
        print(f"Redirecting to new leader at {new_leader}. Retry {retries}/{self.max_retries}.")
    
    def ping(self) -> Any:
        return self.__call_method("ping")

    def get(self, key: str) -> Any:
        return self.__call_method("get", key)

    def set(self, key: str, value: str) -> Any:
        return self.__call_method("set", key, value)

    def strln(self, key: str) -> Any:
        return self.__call_method("strln", key)

    def delete(self, key: str) -> Any:
        return self.__call_method("del", key)

    def append(self, key: str, value: str) -> Any:
        return self.__call_method("append", key, value)