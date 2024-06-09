import json
import xmlrpc.client
from .struct import Address

class App:
    def __init__(self, store, server=None, server_addr=None):
        self.store = store
        self.server = server
        self.server_addr = server_addr

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
                return {"error": "Invalid response from server"}
        else:
            return {"error": "Server not available"}

    def __call_method(self, method, *params):
        while True:
            try:
                func = getattr(self.server, method)
                return func(*params)
            except xmlrpc.client.Fault as fault:
                if fault.faultCode == 505:
                    self.handle_leader_redirect(fault.faultString)
                else:
                    return {"error": "Error connecting to " + fault.faultString}
            except Exception as e:
                return {"error": f"Error calling method {method}: {e}"}

    def handle_leader_redirect(self, leader_addr):
        ip, port = leader_addr.split(':')
        self.server_addr = Address(ip, int(port))
        self.server = xmlrpc.client.ServerProxy(f"http://{self.server_addr.ip}:{self.server_addr.port}")
        print(f"\nRedirecting to new leader at {leader_addr}\n")

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
    
    def request_log(self):
        response = self.execute_request("request_log")
        self.handle_response(response)
