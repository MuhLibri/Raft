import sys
import json

class App:
    def __init__(self, store, server=None, server_addr=None):
        self.store = store
        self.server = server
        self.server_addr = server_addr

    def run(self):
        while True:
            command = input("Enter command: ").strip().split()
            if not command:
                continue

            cmd = command[0].lower()
            args = command[1:]

            if cmd == "ping":
                self.ping()
            elif cmd == "get" and len(args) == 1:
                self.get(args[0])
            elif cmd == "set" and len(args) == 2:
                self.set(args[0], args[1])
            elif cmd == "strln" and len(args) == 1:
                self.strln(args[0])
            elif cmd == "delete" and len(args) == 1:
                self.delete(args[0])
            elif cmd == "append" and len(args) == 2:
                self.append(args[0], args[1])
            elif cmd == "shutdown":
                self.shutdown()
                break
            else:
                print("Invalid command or arguments")

    def ping(self):
        if self.server:
            request = {
                "address": {
                    "ip": self.server_addr.ip,
                    "port": self.server_addr.port
                }
            }
            response = self.server.ping(json.dumps(request))
            print(f"Ping response: {response}")
        else:
            print({"status": "pong"})

    def get(self, key):
        pass

    def set(self, key, value):
        pass

    def strln(self, key):
        pass

    def delete(self, key):
        pass

    def append(self, key, value):
        pass

    def shutdown(self):
        print("Shutting down...")
        sys.exit(0)
