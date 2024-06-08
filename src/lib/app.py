import json
import xmlrpc.client
from .struct import Address

class App:
    def __init__(self, store, server=None, server_addr=None):
        self.store = store
        self.server = server
        self.server_addr = server_addr
        self.max_retries = 3

    def execute_request(self, function_name, *args):
        if self.server:
            request = {
                "function_name": function_name,
                "arguments": args
            }
            response = self.__call_method("execute", json.dumps(request))
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"error": "Invalid response from server"}
        else:
            return {"error": "Server not available"}

    def handle_response(self, response):
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                print(f"Error: Invalid response format: {response}\n")
                return

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

    def __call_method(self, method, *params):
        retries = 0
        while retries < self.max_retries:
            try:
                func = getattr(self.server, method)
                return func(*params)
            except xmlrpc.client.Fault as fault:
                if fault.faultString.startswith("NOT_LEADER"):
                    self.__handle_leader_redirect(fault, retries)
                    retries += 1
                else:
                    print(f"Error calling method {method}: {fault.faultString}\n")
                    return None
            except AttributeError:
                print(f"Method {method} not found on server.\n")
                return None
            except Exception as e:
                print(f"Error calling method {method}: {e}\n")
                return None
        
        print(f"Maximum retries ({self.max_retries}) exceeded for method {method}.\n")
        return None

    def __handle_leader_redirect(self, fault, retries):
        new_leader = fault.faultString.split()[1]
        ip, port = new_leader.split(':')
        self.server_addr = Address(ip, int(port))
        self.server = xmlrpc.client.ServerProxy(f"http://{self.server_addr.ip}:{self.server_addr.port}")
        print(f"Redirecting to new leader at {new_leader}. Retry {retries}/{self.max_retries}.\n")

    def ping(self):
        response = self.execute_request("ping")
        self.handle_response(response)

    def get(self, key):
        response = self.execute_request("get", key)
        self.handle_response(response)

    def set(self, key, value):
        response = self.execute_request("set", key, value)
        self.handle_response(response)

    def strln(self, key):
        response = self.execute_request("strln", key)
        self.handle_response(response)

    def delete(self, key):
        response = self.execute_request("delete", key)
        self.handle_response(response)

    def append(self, key, value):
        response = self.execute_request("append", key, value)
        self.handle_response(response)
