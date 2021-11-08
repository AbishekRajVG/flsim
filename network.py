from py_interface import *
from ctypes import *

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
        ('c', c_int*4)
    ]

# Array structure to hold all 
# client's data in simulation
class Clients(Structure):
    _pack_ = 1
    _fields_ = [
        ('client', Client*4)
    ]


class Network(object):
    def __init__(self, config):
        mempool_key = 1234       # memory pool key, arbitrary integer large than 1000, needs to be changed each time memory size changes
        mem_size = 4096          # memory pool size in bytes
        memblock_key = 2350     # memory block key, need to keep the same in the ns-3 script
        self.config = config      
        self.num_clients = self.config.clients.total
        ns3settings = {'numClients': self.num_clients}     # Command line arguments for ns3
        self.exp = Experiment(mempool_key, mem_size, 'wifi', '../ns-allinone-3.34/ns-3.34')      # Set up the ns-3 environment
        self.exp.reset()                                                                                        # Reset the environment
        self.rl = Ns3AIRL(memblock_key, Clients, Server)
        self.rl2 = Ns3AIRL(memblock_key+5, Clients, Server)
        self.pro = self.exp.run(setting=ns3settings,show_output=True)  
        self.config = config
    
    def access_network(self, clients):
        latency = []
        if not self.rl.isFinish():
            with self.rl as data:
                for i in range(len(clients)):
                    print(str(clients[i].client_id) + " client: " + str(data.env.client[clients[i].client_id].latency))
                    latency.append(data.env.client[clients[i].client_id].latency) #access latency from ns3 simulations
                    data.act.c[0] = 0
                    print(latency)

        return latency

    def send_clients(self, clients):
        arr = c_int * self.num_clients
        a = arr(0,0,0) #reset arr from last transmission
        if not self.rl2.isFinish():
            with self.rl2 as data:
                print("dummy " + str(data.env.client[0].latency))
                print("dummy " + str(data.env.client[1].latency))
                data.act.c = a
                for i in range(len(clients)):
                    #print("client id " + str(clients[i].client_id))
                    #print("i " + str(i))
                    #print("client to send" + str(clients[i].client_id))
                    data.act.c[clients[i].client_id]= 1





    def destroy_network(self):
        #self.pro.wait()
        del self.exp
