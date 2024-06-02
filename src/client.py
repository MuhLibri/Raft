import sys
from xmlrpc.client import ServerProxy
from lib.app import App
from lib.struct import Address
from lib.struct import KVStore

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: client.py ip port")
        exit()

    server_addr = Address(sys.argv[1], int(sys.argv[2]))
    with ServerProxy(f"http://{server_addr.ip}:{server_addr.port}") as server:
        store = KVStore()
        app = App(store, server, server_addr)
        app.run()
