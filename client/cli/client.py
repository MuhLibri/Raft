import json
import sys
from xmlrpc.client import ServerProxy
from lib.app import App
from lib.struct import Address
from lib.struct import KVStore

def shutdown():
    print("Shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: client.py ip port")
        exit()

    address_list : list[Address] = []

    server_addr = Address(sys.argv[1], int(sys.argv[2]))
    server = ServerProxy(f"http://{server_addr.ip}:{server_addr.port}")
    
    try:
        response = json.loads(server.connect())
        for addr in response["list"]:
            address_list.append(Address(addr["ip"], addr["port"]))
        app = App(KVStore(), server, server_addr)
    except Exception as e:
        print(f"Error connecting to server: please input an active server address\n")
        exit()
    
    while True:
        command = input("Enter command: ").strip().split()
        if not command:
            continue

        cmd = command[0].lower()
        args = command[1:]

        try:
            response = json.loads(server.connect())
            address_list.clear()
            for addr in response["list"]:
                address_list.append(Address(addr["ip"], addr["port"]))
        except Exception as e:            
            address_list.remove(server_addr)
            app.handle_leader_redirect(address_list[0].__str__())
            server_addr = address_list[0]
            server = ServerProxy(f"http://{server_addr.ip}:{server_addr.port}")

        if cmd == "ping":
            app.ping()
        elif cmd == "get" and len(args) == 1:
            app.get(args[0])
        elif cmd == "set" and len(args) == 2:
            app.set(args[0], str(args[1]))
        elif cmd == "strln" and len(args) == 1:
            app.strln(args[0])
        elif cmd == "del" and len(args) == 1:
            app.delete(args[0])
        elif cmd == "append" and len(args) == 2:
            app.append(args[0], str(args[1]))
        elif cmd == "append" and len(args) == 1:
            app.append(args[0], None)
        elif cmd == "shutdown":
            shutdown()
            break
        else:
            print("Invalid command or arguments\n")
