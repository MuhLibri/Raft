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

    server_addr = Address(sys.argv[1], int(sys.argv[2]))
    with ServerProxy(f"http://{server_addr.ip}:{server_addr.port}") as server:
        app = App(KVStore(), server, server_addr)
    
    while True:
        command = input("Enter command: ").strip().split()
        if not command:
            continue

        cmd = command[0].lower()
        args = command[1:]

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
