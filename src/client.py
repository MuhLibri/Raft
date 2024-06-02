import sys
from xmlrpc.client import ServerProxy
from lib.app import App
from lib.struct import Address
from lib.struct import KVStore
from lib.key_value_services import KeyValueService

def shutdown():
    print("Shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: client.py ip port")
        exit()

    server_addr = Address(sys.argv[1], int(sys.argv[2]))
    # with ServerProxy(f"http://{server_addr.ip}:{server_addr.port}") as server:
    #     store = KVStore()
    #     app = App(store, server, server_addr)
    #     app.run()
    
    server = ServerProxy(f"http://{server_addr.ip}:{server_addr.port}")
    store = KVStore()
    service = KeyValueService(store, server_addr)
    
    while True:
        command = input("Enter command: ").strip().split()
        if not command:
            continue

        cmd = command[0].lower()
        args = command[1:]

        if cmd == "ping":
            print(service.ping())
        elif cmd == "get" and len(args) == 1:
            print(service.get(args[0]))
        elif cmd == "set" and len(args) == 2:
            print(service.set(args[0], args[1]))
        elif cmd == "strln" and len(args) == 1:
            print(service.strln(args[0]))
        elif cmd == "delete" and len(args) == 1:
            print(service.delete(args[0]))
        elif cmd == "append" and len(args) == 2:
            print(service.append(args[0], args[1]))
        elif cmd == "shutdown":
            shutdown()
            break
        else:
            print("Invalid command or arguments")
    
