import asyncio
import json
import random
import socket
import time
from threading     import Thread
from xmlrpc.client import ServerProxy
from typing        import Any, List
from enum          import Enum
from .struct       import Address
import threading

class RaftNode:
    HEARTBEAT_INTERVAL   = 1
    ELECTION_TIMEOUT_MIN = 1000
    ELECTION_TIMEOUT_MAX = 2000
    FOLLOWER_TIMEOUT_MIN = 500
    FOLLOWER_TIMEOUT_MAX = 1000
    RPC_TIMEOUT          = 0.5
    
    class NodeType(Enum):
        LEADER    = 1
        CANDIDATE = 2
        FOLLOWER  = 3

    # Public Raft Node methods
    def __init__(self, application : Any, addr: Address, contact_addr: Address = None, address_list: List[Address] = []):
        socket.setdefaulttimeout(RaftNode.RPC_TIMEOUT)
        self.address:             Address           = addr
        self.type:                RaftNode.NodeType = RaftNode.NodeType.FOLLOWER
        self.log:                 List[str, str]    = []
        self.app:                 Any               = application
        self.election_term:       int               = 0
        self.cluster_addr_list:   List[Address]     = address_list
        self.cluster_leader_addr: Address           = None
        self.follower_timeout = 0
        self.candidate_timeout = 0
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self.commit_index:        int               = -1
        
        if contact_addr is None:
            # self.cluster_addr_list.append(self.address)
            self.__print_log(f"Cluster Addr List: {self.cluster_addr_list}")
            self.initialization()
        else:
            self.__try_to_apply_membership(contact_addr)

    
    
    def countdown(self, timeout):
        start_timer = time.time()
        while time.time() < start_timer + timeout / 1000:
            if self._stop_event.is_set():
                break
            milis = (start_timer + timeout / 1000 - time.time()) * 1000
            secs, milis = divmod(milis, 1000)
            timer = '{:02d}:{:02d}'.format(int(secs), int(milis))
            # end='\r' in printing timer will replace the previous timer
            self.__print_log(f"Timeout: {timer}", end='\r')
            time.sleep(0.1)
    
    def random_timeout(self, min: int, max: int) -> int:
        return min + (max - min) * random.random()
    
    # Internal Raft Node methods
    def __print_log(self, text: str, end='\n'):
        print(f"[{self.address}] [{time.strftime('%H:%M:%S')}] {text}", end=end)

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
            # print cluster_addr_list
            self.__print_log(f"Cluster Addr List: {self.cluster_addr_list}")
            for node_addr in self.cluster_addr_list:
                if node_addr != self.address:
                    prev_log_index = len(self.log) - 1
                    prev_log_term = self.log[prev_log_index][0] if prev_log_index >= 0 else None
                    entries = [(self.election_term, f"entry-{len(self.log)}")]
                    self.__print_log(f"[Leader] Sending heartbeat to {node_addr}")
                    self.__send_request({
                        "address": self.address,
                        "heartbeat": True,
                        "commit_index": self.commit_index,
                        "term": self.election_term,
                        "prev_log_index": prev_log_index,
                        "prev_log_term": prev_log_term,
                        "entry": entries
                        }, "heartbeat", node_addr)
                    self.log.append(entries[0])
                    self.commit_index += 1
            await asyncio.sleep(RaftNode.HEARTBEAT_INTERVAL)
    
    def __try_to_apply_membership(self, contact_addr: Address) -> bool:
        self.__print_log(f"Trying to apply membership to {contact_addr}")
        redirected_addr = contact_addr
        response = {
            "status": "redirected",
            "address": {
                "ip":   contact_addr.ip,
                "port": contact_addr.port,
            }
        }
        while response["status"] != "success":
            self.__print_log(f"Redirected to {redirected_addr}")
            redirected_addr = Address(response["address"]["ip"], response["address"]["port"])
            try:
                response        = self.__send_request(self.address, "apply_membership", redirected_addr)
            except ConnectionRefusedError:
                self.__print_log(f"Connection refused to {redirected_addr}")
                return False
        self.log                 = response["log"]
        self.cluster_addr_list   = response["cluster_addr_list"]
        self.cluster_leader_addr = redirected_addr
        self.__print_log(f"Membership applied successfully. Cluster Leader: {self.cluster_leader_addr}")
        return True
        # # nyalain heartbeat
        # self.heartbeat_thread = Thread(target=asyncio.run,args=[self.__follower_heartbeat()])
        # self.heartbeat_thread.start()

    def __send_request(self, request: Any, rpc_name: str, addr: Address) -> "json":
        # Warning : This method is blocking
        # try:
        node         = ServerProxy(f"http://{addr.ip}:{addr.port}")
        json_request = json.dumps(request)
        rpc_function = getattr(node, rpc_name)
        self.__print_log(f"JSON Request: {json_request}")
        response     = json.loads(rpc_function(json_request))
        self.__print_log(f"Request: {request}")
        self.__print_log(f"Response: {response}")
        return response
        # except Exception as e:   
            # self.__print_log(f"Error: {e}")
            # return None

    def reset_timeout(self):
        with self._lock:
            self.__print_log("Resetting timeout...")
            self.follower_timeout = self.random_timeout(RaftNode.FOLLOWER_TIMEOUT_MIN, RaftNode.FOLLOWER_TIMEOUT_MAX)
            self.candidate_timeout = self.random_timeout(RaftNode.ELECTION_TIMEOUT_MIN, RaftNode.ELECTION_TIMEOUT_MAX)
            self._stop_event.set()         
    
    def initialization(self):
        # switch case for node type
        if self.type == RaftNode.NodeType.FOLLOWER:
            # timeout follower
            self.__print_log("Starting timeout follower...")
            # random from follower timeout min to follower timeout max
            self.follower_timeout = self.random_timeout(RaftNode.FOLLOWER_TIMEOUT_MIN, RaftNode.FOLLOWER_TIMEOUT_MAX)
            self.countdown(self.follower_timeout)
            self.__print_log("Follower timeout. Be a candidate...")
            self.type = RaftNode.NodeType.CANDIDATE
            self.initialization()
        elif self.type == RaftNode.NodeType.CANDIDATE:
            # timeout candidate
            # choose random from 150 ms to 300 ms
            self.candidate_timeout = RaftNode.ELECTION_TIMEOUT_MIN + (RaftNode.ELECTION_TIMEOUT_MAX - RaftNode.ELECTION_TIMEOUT_MIN) * random.random()
            self.__print_log(f"Starting timeout candidate... {self.candidate_timeout}")
            self.start_election()
            self.countdown(self.candidate_timeout)
            self.initialization()
        else:
            # stop countdown
            self.__print_log("Stopping countdown...")
            self._stop_event.set()
    
    def start_election(self):
        self.__print_log("Starting election...")
        self.election_term += 1
        self.votes_received = 1  # Vote for self
        request = {"term": self.election_term, "candidate_id": self.address}

        for node_addr in self.cluster_addr_list:
            if node_addr != self.address:
                self.__print_log(f"Sending request vote to {node_addr}")
                response = self.__send_request(request, "request_vote", node_addr)
                if response["vote_granted"]:
                    self.__print_log(f"Server {self.address} received vote from {node_addr}")
                    self.votes_received += 1

        if self.votes_received > len(self.cluster_addr_list) // 2:
            self.__print_log(f"self.votes_received: {self.votes_received}")
            self.__print_log(f"Server {self.address} is elected as leader")
            self.__initialize_as_leader()
            self.initialization()
            
    # Inter-node RPCs
    def heartbeat(self, json_request: str) -> "json":
        # TODO : Implement heartbeat
        request = json.loads(json_request)
        self.__print_log(f"Received heartbeat from {request['address']}")
        # reset timeout
        self.reset_timeout()
        response = {
            "heartbeat_response": "ack", 
            "address": {
                "ip": self.address.ip, 
                "port": self.address.port}}
        return json.dumps(response)

    def ping(self, json_request: str) -> "json":
        request = json.loads(json_request)
        self.__print_log(f"Received ping from {request['address']}")
        success = self.append_entries(request['term'], request['address'], request['prev_log_index'], request['prev_log_term'], request['entry'], request['commit_index'])
        if success:
            self.log.append(request['entry'][0])
            self.commit_index += 1
        response = {
            "status": "success", 
            "ping_response": "pong",
            "address": {
                "ip": self.address.ip, 
                "port": self.address.port}}
        return json.dumps(response)
    
    def append_entries(self, term, prev_log_index, prev_log_term, entry, commit_index):
        if term < self.election_term:
            return False
        
        self.election_term = term
        
        if prev_log_index >= 0 and (prev_log_index >= len(self.log) or self.log[prev_log_index][0] != prev_log_term):
            return False
        
        self.log = self.log[:prev_log_index + 1] + entry
        
        if commit_index > self.commit_index:
            self.commit_index = min(commit_index, len(self.log) - 1)
        
        return True

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
        self.__print_log(f"Received apply_membership request from {json_request}")
        self.__print_log(f"Current cluster_addr_list: {self.cluster_addr_list}")
        request = json.loads(json_request)
        self.cluster_addr_list.append(Address(request["ip"], request["port"]))
        self.__print_log(f"Updated cluster_addr_list: {self.cluster_addr_list}")
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