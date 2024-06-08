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
                print(f"Error: Invalid response format: {response}")
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
            print(f"Error: Unexpected response type: {type(response)}")

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
