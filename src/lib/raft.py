import asyncio
import json
import socket
from threading     import Thread
import time
from xmlrpc.client import ServerProxy
from typing        import Any, List
from enum          import Enum
from .struct       import Address



class RaftNode:
    HEARTBEAT_INTERVAL   = 1
    ELECTION_TIMEOUT_MIN = 2
    ELECTION_TIMEOUT_MAX = 3
    RPC_TIMEOUT          = 0.5

    class NodeType(Enum):
        LEADER    = 1
        CANDIDATE = 2
        FOLLOWER  = 3

    def __init__(self, application : Any, addr: Address, contact_addr: Address = None):
        socket.setdefaulttimeout(RaftNode.RPC_TIMEOUT)
        self.address:             Address           = addr
        self.type:                RaftNode.NodeType = RaftNode.NodeType.FOLLOWER
        self.log:                 List[str, str]    = []
        self.app:                 Any               = application
        self.election_term:       int               = 0
        self.cluster_addr_list:   List[Address]     = []
        self.cluster_leader_addr: Address           = None
        if contact_addr is None:
            self.cluster_addr_list.append(self.address)
            self.__initialize_as_leader()
        else:
            self.__try_to_apply_membership(contact_addr)



    # Internal Raft Node methods
    def __print_log(self, text: str):
        print(f"[{self.address}] [{time.strftime('%H:%M:%S')}] {text}")

    def __initialize_as_leader(self):
        self.__print_log("Initialize as leader node...")
        self.cluster_leader_addr = self.address
        self.type                = RaftNode.NodeType.LEADER
        request = {
            "cluster_leader_addr": self.address
        }
        # TODO : Inform to all node this is new leader
        for node_addr in self.cluster_addr_list:
            if node_addr != self.address:
                self.__send_request(request, "notify_leader", node_addr)
        
        self.heartbeat_thread = Thread(target=asyncio.run,args=[self.__leader_heartbeat()])
        self.heartbeat_thread.start()

    async def __leader_heartbeat(self):
        # TODO : Send periodic heartbeat
        while True:
            self.__print_log("[Leader] Sending heartbeat...")
            for node_addr in self.cluster_addr_list:
                if node_addr != self.address:
                    self.__send_request({"heartbeat": True}, "heartbeat", node_addr)
            await asyncio.sleep(RaftNode.HEARTBEAT_INTERVAL)

    def __try_to_apply_membership(self, contact_addr: Address):
        redirected_addr = contact_addr
        response = {
            "status": "redirected",
            "address": {
                "ip":   contact_addr.ip,
                "port": contact_addr.port,
            }
        }
        while response["status"] != "success":
            redirected_addr = Address(response["address"]["ip"], response["address"]["port"])
            try:
                response        = self.__send_request(self.address, "apply_membership", redirected_addr)
            except ConnectionRefusedError:
                self.__print_log(f"Connection refused to {redirected_addr}")
        self.log                 = response["log"]
        self.cluster_addr_list   = response["cluster_addr_list"]
        self.cluster_leader_addr = redirected_addr

    def __send_request(self, request: Any, rpc_name: str, addr: Address) -> "json":
        # Warning : This method is blocking
        node         = ServerProxy(f"http://{addr.ip}:{addr.port}")
        json_request = json.dumps(request)
        rpc_function = getattr(node, rpc_name)
        response     = json.loads(rpc_function(json_request))
        self.__print_log(f"Request: {request}")
        self.__print_log(f"Response: {response}")
        return response

    def start_election(self):
        self.election_term += 1
        self.type = RaftNode.NodeType.CANDIDATE
        self.votes_received = 1  # Vote for self
        request = {"term": self.election_term, "candidate_id": self.address}

        for node_addr in self.cluster_addr_list:
            if node_addr != self.address:
                response = self.__send_request(request, "request_vote", node_addr)
                if response["vote_granted"]:
                    self.votes_received += 1

        if self.votes_received > len(self.cluster_addr_list) // 2:
            self.__initialize_as_leader()
    
    # Inter-node RPCs
    def heartbeat(self, json_request: str) -> "json":
        # TODO : Implement heartbeat
        request = json.loads(json_request)
        self.__print_log(f"[Follower] Received heartbeat from {request['address']}")
        response = {
            "heartbeat_response": "ack", 
            "address": {
                "ip": self.address.ip, 
                "port": self.address.port}}
        return json.dumps(response)

    def request_vote(self, json_request: str) -> "json":
        request = json.loads(json_request)
        vote_granted = False
        if request["term"] > self.election_term:
            self.election_term = request["term"]
            self.type          = RaftNode.NodeType.FOLLOWER
            vote_granted       = True
            
        response = {
            "term":        self.election_term,
            "vote_granted": vote_granted,
        }
        
        return json.dumps(response)

    def notify_leader(self, json_request: str) -> "json":
        request = json.loads(json_request)
        self.cluster_leader_addr = Address(request["cluster_leader_addr"]["ip"], request["cluster_leader_addr"]["port"])
        self.type = RaftNode.NodeType.FOLLOWER
        response = {"status": "success"}
        return json.dumps(response)
    
    def apply_membership(self, json_request: str) -> "json":
        request = json.loads(json_request)
        self.cluster_addr_list.append(Address(request["ip"], request["port"]))
        response = {
            "status": "success", 
            "log": self.log, 
            "cluster_addr_list": self.cluster_addr_list}
        return json.dumps(response)
    
    # Client RPCs
    def execute(self, json_request: str) -> "json":
        request = json.loads(json_request)
        # TODO : Implement execute
        response = {"status": "success"}
        return json.dumps(response)