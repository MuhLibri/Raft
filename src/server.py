import sys
import os
from lib.struct import Address
from lib          import RaftNode
from xmlrpc.server import SimpleXMLRPCServer
from lib           import App
from lib.struct    import KVStore



def start_serving(addr: Address, contact_node_addr: Address, address_list: list[Address]):
    print(f"Starting Raft Server at {addr.ip}:{addr.port}")
    with SimpleXMLRPCServer((addr.ip, addr.port)) as server:
        server.register_introspection_functions()
        server.register_instance(RaftNode(KVStore(), addr, contact_node_addr, address_list))
        server.serve_forever()

def read_address_list(filename: str) -> list[Address]:
	path = os.path.join(os.getcwd(), filename)
	print("Path:", path)
	address_list = []
	with open(path, "r") as file:
		for line in file:
			ip, port = line.strip().split(" ")
			# each address should be unique
			address = Address(ip, int(port))
			if address not in address_list:
				address_list.append(address)
	print("Address List:", address_list) 
	return address_list

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: server.py ip port [contact_ip] [contact_port]")
        exit()
    # check the third argument, if third is address_list, then parse the address_list
    address_list : list[Address] = []
    contact_addr = None
    
    # read the address_list from the file
    # if the last argument is not membership, then read the address_list
    if sys.argv[-1] != "membership":
        address_list = read_address_list("src\\address.txt")
    server_addr = Address(sys.argv[1], int(sys.argv[2]))
    if len(sys.argv) == 6:
        print("Contact Address:", sys.argv[3], sys.argv[4])
        contact_addr = Address(sys.argv[3], int(sys.argv[4]))

    start_serving(server_addr, contact_addr, address_list)

# def start_election(addr: Address, contact_node_addr: Address):
#     raft_node = RaftNode(KVStore(), addr, contact_node_addr)
#     raft_node.start_election()

# if __name__ == "__main__":
#     if len(sys.argv) < 3:
#         print("Usage: server.py ip port [contact_ip] [contact_port] [start_election]")
#         exit()

#     contact_addr = None
#     if len(sys.argv) >= 5:
#         contact_addr = Address(sys.argv[3], int(sys.argv[4]))
    
#     server_addr = Address(sys.argv[1], int(sys.argv[2]))

#     if len(sys.argv) == 6 and sys.argv[5] == "start_election":
#         start_election(server_addr, contact_addr)
#     else:
#         start_serving(server_addr, contact_addr)
