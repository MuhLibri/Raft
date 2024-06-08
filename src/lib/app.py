import json

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
            response = self.server.execute(json.dumps(request))
            return json.loads(response)
        else:
            return {"error": "Server not available"}

    def ping(self):
        response = self.execute_request("ping")
        if response.get("error"):
            print(response["error"], "\n")
        else:
            print(response["value"], "\n")

    def get(self, key):
        response = self.execute_request("get", key)
        if response.get("error"):
            print(response["error"], "\n")
        else:
            print(response["value"], "\n")

    def set(self, key, value):
        response = self.execute_request("set", key, value)
        if response.get("error"):
            print(response["error"], "\n")
        else:
            print(response["status"], "\n")

    def strln(self, key):
        response = self.execute_request("strln", key)
        if response.get("error"):
            print(response["error"], "\n")
        else:
            print(response["value"], "\n")

    def delete(self, key):
        response = self.execute_request("delete", key)
        if response.get("error"):
            print(response["error"], "\n")
        else:
            print(response["value"], "\n")

    def append(self, key, value):
        response = self.execute_request("append", key, value)
        if response.get("error"):
            print(response["error"], "\n")
        else:
            print(response["status"], "\n")
