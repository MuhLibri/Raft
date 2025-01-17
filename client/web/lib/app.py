import json
import xmlrpc.client
from .struct import Address

class App:
    def __init__(self, server=None, server_addr=None):
        self.server: xmlrpc.client.ServerProxy = server
        self.server_addr: Address = server_addr
        self.server_addr_list: list[Address] = []
        self.server_addr_list.append(server_addr)

    def execute_request(self, function_name, *args):
        if self.server:
            request = {
                "function_name": function_name,
                "arguments": args
            }
            response = self.__call_method("execute", json.dumps(request))
            try:
                if isinstance(response, str):
                    return json.loads(response)
                else:
                    return response
            except json.JSONDecodeError:
                return {"error": "Invalid response from server",
                        "server_ip": self.server_addr.ip,
                        "server_port": self.server_addr.port
                        }
        else:
            return {"error": "Server not available",
                    "server_ip": self.server_addr.ip,
                    "server_port": self.server_addr.port}

    def __call_method(self, method, *params):
        while True:
            try:
                try:
                    response = json.loads(self.server.connect())
                    for addr in response["list"]:
                        self.server_addr_list.append(Address(addr["ip"], addr["port"]))
                except Exception as e:
                    self.server_addr_list.remove(self.server_addr)
                    self.handle_leader_redirect(self.server_addr_list[0].__str__())
                    
                func = getattr(self.server, method)
                return func(*params)
            except xmlrpc.client.Fault as fault:
                if fault.faultCode == 505:
                    self.handle_leader_redirect(fault.faultString)
                else:
                    return {"error": "Error connecting to " + fault.faultString,
                            "server_ip": self.server_addr.ip,
                            "server_port": self.server_addr.port}
            except Exception as e:
                return {"error": f"Error calling method {method}: {e}",
                        "server_ip": self.server_addr.ip,
                        "server_port": self.server_addr.port}

    def handle_leader_redirect(self, leader_addr):
        ip, port = leader_addr.split(':')
        self.server_addr = Address(ip, int(port))
        self.server = xmlrpc.client.ServerProxy(f"http://{self.server_addr.ip}:{self.server_addr.port}")
        if self.server_addr not in self.server_addr_list:
            self.server_addr_list.append(self.server_addr)
        print(f"\nRedirecting to new leader at {leader_addr}\n")

    def handle_response(self, response) -> dict:
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                print(f"Error: Invalid response format: {response}\n")
                return {"error": "Invalid response format",
                        "server_ip": self.server_addr.ip,
                        "server_port": self.server_addr.port}

        if isinstance(response, dict):
            if "error" in response:
                print(f"Error: {response['error']}\n")
                
            else:
                if "value" in response:
                    print(f"{response['value']}\n")
                elif "status" in response:
                    print(f"{response['status']}\n")
        else:
            print(f"Error: Unexpected response type: {type(response)}\n")
            
        response.update({
            "server_ip": self.server_addr.ip,
            "server_port": self.server_addr.port
        })

        print(f"Response: {response}\n")
        return response  # Mengembalikan respons jika tidak terdapat error
    
    def __response_wrapper(self, response: dict):
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                print(f"Error: Invalid response format: {response}\n")
                return {"error": "Invalid response format",
                        "server_ip": self.server_addr.ip,
                        "server_port": self.server_addr.port}
        
        return response.update({"server_ip": self.server_addr.ip, "server_port": self.server_addr.port})

    def ping(self):
        response = self.execute_request("ping")
        return self.handle_response(response)

    def get(self, key):
        response = self.execute_request("get", key)
        return self.handle_response(response)

    def set(self, key, value):
        response = self.execute_request("set", key, value)
        return self.handle_response(response)

    def strln(self, key):
        response = self.execute_request("strln", key)
        return self.handle_response(response)

    def delete(self, key):
        response = self.execute_request("delete", key)
        return self.handle_response(response)

    def append(self, key, value):
        response = self.execute_request("append", key, value)
        return self.handle_response(response)
    
    def request_log(self):
        response = self.execute_request("request_log")
        return self.handle_response(response)