import sys
import asyncio
import json
import random
import socket
import time
import threading
from xmlrpc.client import ServerProxy, Fault
from typing        import List, Tuple, Dict
from enum          import Enum
from .struct       import Address
from .struct       import KVStore

class RaftNode:
    HEARTBEAT_INTERVAL   = 1
    ELECTION_TIMEOUT_MIN = 2000
    ELECTION_TIMEOUT_MAX = 4000
    FOLLOWER_TIMEOUT_MIN = 1000
    FOLLOWER_TIMEOUT_MAX = 2000
    RPC_TIMEOUT          = 1
    
    class NodeType(Enum):
        LEADER    = 1
        CANDIDATE = 2
        FOLLOWER  = 3

    # Public Raft Node methods
    def __init__(self, store: KVStore, addr: Address, contact_addr: Address = None, address_list: List[Address] = []):
        socket.setdefaulttimeout(RaftNode.RPC_TIMEOUT)
        self.address:             Address               = addr
        self.type:                RaftNode.NodeType     = RaftNode.NodeType.FOLLOWER
        self.log:                 List[Tuple[int, str]] = []
        self.store:               KVStore               = store
        self.election_term:       int                   = 0
        self.cluster_addr_list:   List[Address]         = address_list
        self.cluster_leader_addr: Address               = None
        self._stop_event                                = threading.Event()
        self._lock                                      = threading.Lock()
        self.commit_index:        int                   = -1
        self.match_index:         Dict[Address, int]    = {}

        if contact_addr is None:
            self.__print_log(f"[Leader] Cluster Addr List: {self.cluster_addr_list}")
            self.initialization()
        else:
            self.cluster_addr_list.append(self.address)
            self.__try_to_apply_membership(contact_addr)
    
    def connect(self) -> "json":
        response = {
            "list": self.cluster_addr_list
        }
        
        return json.dumps(response)

    def random_timeout(self, min: int, max: int) -> int:
        return min + (max - min) * random.random()
    
    def reset_timeout(self):
        with self._lock:
            self.__print_log("Resetting timeout...")
            self._stop_event.set()  
    
    def countdown(self, timeout_min, timeout_max) -> bool:
        while True:
            self._stop_event.clear()
            with self._lock:
                timeout = self.random_timeout(timeout_min, timeout_max)
            start_timer = time.time()
            self.__print_log(f"Starting timeout: {timeout} ms")
            while time.time() < start_timer + timeout / 1000:
                if self._stop_event.is_set():
                    break
                milis = (start_timer + timeout / 1000 - time.time()) * 1000
                secs, milis = divmod(milis, 1000)
                timer = '{:02d}:{:02d}'.format(int(secs), int(milis))
                self.__print_log(f"Timeout: {timer}", end="\r")
                time.sleep(0.1)
            if not self._stop_event.is_set():
                break
        if self.type == RaftNode.NodeType.FOLLOWER:
            self.__print_log("Follower timeout. Be a candidate...")
            self.type = RaftNode.NodeType.CANDIDATE
        self.initialization()

    def start_countdown(self, timeout_countdown_min, timeout_countdown_max):
        self._thread = threading.Thread(target=self.countdown, args=(timeout_countdown_min, timeout_countdown_max))
        if self._thread.is_alive():
            self._thread.join()
        else:
            self._thread.start()

    # Internal Raft Node methods
    def __print_log(self, text: str, end='\n'):
        print(f"[{self.address}] [{time.strftime('%H:%M:%S')}] {text}", end=end)

    def __initialize_as_leader(self):
        self.__print_log("Initialize as leader node...")
        self.cluster_leader_addr = self.address
        self.type                = RaftNode.NodeType.LEADER

        for addr in self.cluster_addr_list:
            if addr != self.address:
                # Initialize match index for each follower
                self.match_index[addr] = -1  

        request = {"cluster_leader_addr": self.address}

        for node_addr in self.cluster_addr_list:
            if node_addr != self.address:
                self.__send_request(request, "notify_leader", node_addr)
        
        self.heartbeat_thread = threading.Thread(target=asyncio.run, args=[self.__leader_heartbeat()])
        self.heartbeat_thread.start()

    async def __leader_heartbeat(self, func="heartbeat", args=None):
        while (self.type == RaftNode.NodeType.LEADER):
            self.__print_log(f"[Leader] Sending {func}...")
            self.__print_log(f"[Leader] Cluster Addr List: {self.cluster_addr_list}")
            ack_count = 1
            responses = []

            prev_log_index = len(self.log) - 1
            prev_log_term = self.log[prev_log_index][0] if prev_log_index >= 0 else None
            entries = [(self.election_term, f"entry-{len(self.log)}")]

            for node_addr in self.cluster_addr_list:
                if node_addr != self.address:
                    self.__print_log(f"[Leader] Sending {func} to {node_addr}")

                    # Apply leader cluster_addr_list to all followers
                    # updated_cluster_request = {"cluster_addr_list": self.cluster_addr_list}
                    # self.__send_request(updated_cluster_request, "update_cluster_addr_list", node_addr)
                    
                    response = self.__send_request({
                        "log": self.log,
                        "address": self.address,
                        "heartbeat": True,
                        "cluster_addr_list": self.cluster_addr_list,
                        "commit_index": self.commit_index,
                        "term": self.election_term,
                        "prev_log_index": prev_log_index,
                        "prev_log_term": prev_log_term,
                        "entry": entries,
                        "function_name": func,
                        "arguments": args
                    }, "heartbeat" if func == "heartbeat" else "follower_execute", node_addr)
                    responses.append(response)

                    if response:
                        if response.get("status") == "success":
                            ack_count += 1
                            self.match_index[node_addr] = prev_log_index + len(entries)
                        else:
                            self.__print_log(f"Received error from {node_addr}: {response.get('error')}")

            # Ensure entries are committed if a majority of followers have acknowledged
            if ack_count > len(self.cluster_addr_list) // 2:
                self.__print_log(f"[Leader] Entries committed. Acknowledged by majority of followers.")
                self.log.append(entries[0])
                self.commit_index += 1
            else:
                self.__print_log(f"[Leader] Entries not committed. Acknowledged by {ack_count} out of {len(self.cluster_addr_list)} followers.")

            if func != "heartbeat":
                if ack_count > len(self.cluster_addr_list) // 2:
                    return True
                else:
                    return False

            await asyncio.sleep(RaftNode.HEARTBEAT_INTERVAL)

    
    def get_leader(self) -> "json":
        response = {
            "status": "success", 
            "addr_leader": {
                "ip":   self.cluster_leader_addr.ip,
                "port": self.cluster_leader_addr.port
            }
        }
        return json.dumps(response)

    def __try_to_get_leader(self, contact_addr: Address):
        try:
            response        = self.__send_request(None, "get_leader", contact_addr)
            self.__print_log(f"Response: {response}")
            if (response != None):
                return Address(response['addr_leader']['ip'], response['addr_leader']['port'])
            else:
                self.__print_log(f"Error getting leader from {contact_addr}")
                return None
        
        except ConnectionRefusedError:
            self.__print_log(f"Connection refused to {contact_addr}")
            return False

    def __try_to_apply_membership(self, contact_addr: Address) -> bool:
        contact_addr = self.__try_to_get_leader(contact_addr)
        time.sleep(RaftNode.FOLLOWER_TIMEOUT_MAX / 1000)
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
                if (response != None):
                    self.log                 = response["log"]
                    self.cluster_addr_list   = response["cluster_addr_list"]
                    self.cluster_leader_addr = redirected_addr
                    self.__print_log(f"Membership applied successfully. Cluster Leader: {self.cluster_leader_addr}")
                    self.initialization()
                    return True
                else:
                    self.__print_log(f"Error applying membership to {redirected_addr}")
                    return False
            
            except ConnectionRefusedError:
                self.__print_log(f"Connection refused to {redirected_addr}")
                return False

    def __send_request(self, request: dict, rpc_name: str, addr: Address) -> "json":
        # Warning : This method is blocking
        try:
            node         = ServerProxy(f"http://{addr.ip}:{addr.port}")
            json_request = json.dumps(request)
            rpc_function = getattr(node, rpc_name)
            response     = json.loads(rpc_function(json_request)) if request else json.loads(rpc_function())
            # self.__print_log(f"Request: {request}")
            # self.__print_log(f"Response: {response}")
            return response

        except Exception as e: 
            self.__print_log(f"rpc_name: {rpc_name}")
            self.__print_log(f"Error: {e}")
            return None
    
    def initialization(self):
        # switch case for node type
        if self.type == RaftNode.NodeType.FOLLOWER:
            # timeout follower
            self.__print_log("Starting timeout follower...")
            # random from follower timeout min to follower timeout max
            self.start_countdown(RaftNode.FOLLOWER_TIMEOUT_MIN, RaftNode.FOLLOWER_TIMEOUT_MAX)
        elif self.type == RaftNode.NodeType.CANDIDATE:
            # timeout candidate
            # self._election_thread = threading.Thread(target=self.start_election)
            # self._election_thread.start()
            self.start_election()
            self.start_countdown(RaftNode.ELECTION_TIMEOUT_MIN, RaftNode.ELECTION_TIMEOUT_MAX)
        else:
            # stop countdown
            self.__print_log("Stopping countdown...")
            self._stop_event.set()
    
    def start_election(self):
        self.__print_log("Starting election...")
        self.election_term += 1
        self.votes_received = 1  # vote for self
        request = {"term": self.election_term, "candidate_id": self.address}

        for node_addr in self.cluster_addr_list:
            if node_addr != self.address:
                self.__print_log(f"Sending request vote to {node_addr}")
                response = self.__send_request(request, "request_vote", node_addr)
                if response == None:
                    # erase node from cluster_addr_list
                    # self.cluster_addr_list.remove(node_addr)
                    continue
                if response["vote_granted"]:
                    self.__print_log(f"Server {self.address} received vote from {node_addr}")
                    self.votes_received += 1

        if self.votes_received > len(self.cluster_addr_list) // 2:
            self.__print_log(f"cluster_addr_list: {self.cluster_addr_list}")
            self.__print_log(f"self.votes_received: {self.votes_received} > {len(self.cluster_addr_list) // 2} = len(self.cluster_addr_list) // 2")
            self.__print_log(f"Server {self.address} is elected as leader")
            self.__initialize_as_leader()
            self.initialization()
    
    # Inter-node RPCs
    def heartbeat(self, json_request: str) -> "json":
        request = json.loads(json_request)

        self.__print_log(f"Received heartbeat from {request['address']}")
        self.__print_log(f"Current cluster address list: {self.cluster_addr_list}")
        # Assign cluster_leader_addr
        # self.cluster_addr_list = request['cluster_addr_list']

        # reset timeout
        term = request['term']
        if term >= self.election_term:
            self.reset_timeout()
            if (self.type == RaftNode.NodeType.LEADER):
                self.type = RaftNode.NodeType.FOLLOWER
                # self.initialization()
            self.type = RaftNode.NodeType.FOLLOWER
            entries = request['entry']
            prev_log_index = request['prev_log_index']
            prev_log_term = request['prev_log_term']
            
            # Check if prev_log_index is within the bounds of self.log
            if prev_log_index == -1 or (0 <= prev_log_index < len(self.log) and self.log[prev_log_index][0] == prev_log_term):
                self.log = self.log[:prev_log_index + 1] + entries
                if request['commit_index'] > self.commit_index:
                    self.commit_index = min(request['commit_index'], len(self.log) - 1)
                self.__print_log(f"Appended entries to log: {entries}")
                success = True
            else:
                success = False
        else:
            success = False

        if success:
            response = {
                "status": "success",
                "term": self.election_term,
                "match_index": len(self.log) - 1
            }
        else:
            response = {
                "status": "error",
                "term": self.election_term,
                "match_index": len(self.log) - 1
            }

        return json.dumps(response)
    
    def append_entries(self, term, prev_log_index, prev_log_term, entry, commit_index):
        if term < self.election_term:
            return False
        
        self.election_term = term
        
        # Fix bounds check here
        if prev_log_index == -1 or (prev_log_index >= 0 and prev_log_index < len(self.log) and self.log[prev_log_index][0] == prev_log_term):
            self.log = self.log[:prev_log_index + 1] + entry
            if commit_index > self.commit_index:
                self.commit_index = min(commit_index, len(self.log) - 1)
            return True
        else:
            return False

    def request_vote(self, json_request: str) -> "json":
        request = json.loads(json_request)
        vote_granted = False
        if request["term"] > self.election_term:
            self.election_term = request["term"]
            if (self.type == RaftNode.NodeType.LEADER):
                self.type = RaftNode.NodeType.FOLLOWER
                # self.initialization()
            self.type          = RaftNode.NodeType.FOLLOWER
            vote_granted       = True
            
        response = {
            "term":        self.election_term,
            "vote_granted": vote_granted,
        }
        
        self.__print_log(f"Responding to vote request: {response}")
        
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

        # apply updated cluster_addr_list to all nodes
        # make a new thread to apply updated cluster_addr_list to all nodes
        self._cluster_update_thread = threading.Thread(target=self.leader_update_cluster_addr_list)
        self._cluster_update_thread.start()

        
        response = {
            "status": "success", 
            "log": self.log, 
            "cluster_addr_list": self.cluster_addr_list}
        
        return json.dumps(response)
    
    def leader_update_cluster_addr_list(self):
        for node_addr in self.cluster_addr_list:
            if node_addr != self.address:
                updated_cluster_request = {"cluster_addr_list": self.cluster_addr_list}
                self.__send_request(updated_cluster_request, "update_cluster_addr_list", node_addr)
        self.__print_log(f"Leader finished updating cluster_addr_list: {self.cluster_addr_list}")
    
    def update_cluster_addr_list(self, json_request: str) -> "json":
        request = json.loads(json_request)
        request_cluster_addr_list = request["cluster_addr_list"]
        self.cluster_addr_list = [Address(addr["ip"], addr["port"]) for addr in request_cluster_addr_list]
        self.__print_log(f"Updated cluster_addr_list: {self.cluster_addr_list}")
        response = {"status": "success"}
        return json.dumps(response)
    
    # Client RPCs
    def execute(self, json_request: str) -> str:
        request = json.loads(json_request)
        function_name = request.get("function_name")
        if function_name:
            function_args = request.get("arguments", [])
            if hasattr(self, function_name):
                function = getattr(self, function_name)
                
                if self.type == RaftNode.NodeType.LEADER:
                    result_event = threading.Event()
                    heartbeat_result = {"success": False}

                    def run_asyncio_coroutine(coroutine, *args):
                        if sys.platform == 'win32':
                            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(coroutine(*args))
                        loop.close()
                        return result

                    def heartbeat_wrapper():
                        try:
                            success = run_asyncio_coroutine(self.__leader_heartbeat, function_name, function_args)
                            heartbeat_result["success"] = success
                        finally:
                            result_event.set()

                    heartbeat_thread = threading.Thread(target=heartbeat_wrapper)
                    heartbeat_thread.start()

                    # Wait for the heartbeat thread to complete
                    result_event.wait()

                    if heartbeat_result["success"]:
                        response = function(*function_args)
                        return json.dumps(response)
                    else:
                        return json.dumps({"error": "Failed to send task to followers"})
                else:
                    raise Fault(505, f"{self.cluster_leader_addr}")
            else:
                return json.dumps({"error": f"Function '{function_name}' not found in RaftNode class"})
        else:
            return json.dumps({"error": "No function name provided in request"})

    
    def follower_execute(self, json_request: str) -> "json":
        request = json.loads(json_request)

        self.__print_log(f"Received execute request from {request['address']}")
        
        success = self.append_entries(request['term'], request['prev_log_index'], request['prev_log_term'], request['entry'], request['commit_index'])

        if success:
            self.log.append(request['entry'][0])
            self.commit_index += 1

        function_name = request.get("function_name")
        if function_name:
            function_args = request.get("arguments", [])
            if hasattr(self, function_name):
                function = getattr(self, function_name)
                function(*function_args)
                self.reset_timeout()
                self.__print_log(f"Executed task: {function_name}({', '.join(str(arg) for arg in function_args)})")
                response = {
                    "status": "success",
                    "term": self.election_term,
                    "match_index": len(self.log) - 1
                }
                return json.dumps(response)
            else:
                error_msg = f"Function '{function_name}' not found in RaftNode class"
                self.__print_log(error_msg)
                return json.dumps({"error": error_msg})
        else:
            error_msg = "No function name provided in request"
            self.__print_log(error_msg)
            return json.dumps({"error": error_msg})
    
    def ping(self) -> "json":

        response = {
            "status": "success", 
            "value": self.store.ping()
        }
                
        return json.dumps(response)
    
    def get(self, key: str) -> "json":
        value = self.store.get(key)

        if value is None:
            response = {
                "status": "error", 
                "error": "Key not found"
            }
        else:
            response = {
                "status": "success", 
                "value": value
            }
        
        return json.dumps(response)
    
    def set(self, key: str, value: str) -> "json":
        status = self.store.set(key, value)
        
        if status is None:
            response = {
                "status": "error", 
                "error": "Key not found"
            }
        else:
            response = {
                "status": status
            }
        
        return json.dumps(response)
    
    def strln(self, key: str) -> "json":
        value = self.store.strln(key)
        
        if value is None:
            response = {
                "status": "error", 
                "error": "Key not found"
            }
        else:
            response = {
                "status": "success", 
                "value": value
            }
        
        return json.dumps(response)
    
    def delete(self, key: str) -> "json":
        status = self.store.delete(key)
        
        if status is None:
            response = {
                "status": "error", 
                "error": "Key not found"
            }
        else:
            response = {
                "status": "success",
                "value": status
            }
        
        return json.dumps(response)
    
    def append(self, key: str, value: str) -> "json":
        status = self.store.append(key, value)
        
        if status is None:
            response = {
                "status": "error", 
                "error": "Error appending value"
            }
        else:
            response = {
                "status": status
            }
        
        return json.dumps(response)
