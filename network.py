from py_interface import *
from ctypes import *
import socket, struct

TCP_IP = '127.0.0.1'
TCP_PORT = 8080

# Shared Memory Structure to represent
# each client's data
#Need to rename
class Client(Structure):
    _pack_ = 1
    _fields_ = [
        ('latency', c_double)
    ]

# Shared memory structure to represent
# some result that needs to be communicated 
# back to ns3 (currently none)
class Server(Structure):
    _pack_ = 1
    _fields_ = [
        ('c', c_int*10)
    ]

# Array structure to hold all 
# client's data in simulation
class Clients(Structure):
    _pack_ = 1
    _fields_ = [
        ('client', Client*10)
    ]


class Network(object):
    def __init__(self, config):
        mempool_key = 1234       # memory pool key, arbitrary integer large than 1000, needs to be changed each time memory size changes
        mem_size = 4096          # memory pool size in bytes
        memblock_key = 2370    # memory block key, need to keep the same in the ns-3 script
        self.config = config      
        self.num_clients = self.config.clients.total
        ns3settings = {'numClients': self.num_clients}     # Command line arguments for ns3
        self.exp = Experiment(mempool_key, mem_size, 'wifi_exp', '../ns-allinone-3.34/ns-3.34')      # Set up the ns-3 environment
        self.exp.reset()                                                                                        # Reset the environment
        self.rl = Ns3AIRL(memblock_key, Clients, Server)
        self.rl2 = Ns3AIRL(memblock_key+5, Clients, Server)
        self.pro = self.exp.run(setting=ns3settings,show_output=True)  
        self.config = config

    def parse_clients(self, clients):
        clients_to_send = [0 for _ in range(self.num_clients)]
        for j in range(len(clients)):
            clients_to_send[j] = 1
        return clients_to_send


    def connect(self):
        self.s = socket.create_connection((TCP_IP,TCP_PORT,))

    def sendRequest(self, *, requestType: int, array: list):
        print("sending")
        print(array)
        message = struct.pack("II", requestType, len(array) )
        self.s.send(message)
        #for the total number of clients
            # is the index in lit at client.id equal
        for ele in array:
            self.s.send(struct.pack("I", ele))

        resp = self.s.recv(8)
        print("resp")
        print(resp)
        if len(resp) < 8:
            print(len(resp), resp)
        command, nItems = struct.unpack("II", resp)
        ret = {
            "roundTime": [],
            "throughput": []
        }
        for i in range(nItems):
            dr = self.s.recv(8*2)
            roundTime, throughput = struct.unpack("dd", dr)
            ret["roundTime"].append(roundTime)
            ret["throughput"].append(throughput)
        return ret

    def disconnect(self):
        self.sendRequest(requestType=2, array=[])
        self.s.close()

    def destroy_network(self):
        #self.pro.wait()
        del self.exp
