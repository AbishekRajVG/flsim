from py_interface import *
from ctypes import *

# Shared Memory Structure to represent
# each client's data
#Need to rename
class Env(Structure):
    _pack_ = 1
    _fields_ = [
        ('datarate', c_double),
        ('latency', c_double),
    ]

# Shared memory structure to represent
# some result that needs to be communicated 
# back to ns3 (currently none)
class Act(Structure):
    _pack_ = 1
    _fields_ = [
        ('c', c_double)
    ]

# Array structure to hold all 
# client's data in simulation
class Array(Structure):
    _pack_ = 1
    _fields_ = [
        ('env', Env*2)
    ]


class Network(object):
    def __init__(self, config):
        mempool_key = 1234       # memory pool key, arbitrary integer large than 1000, needs to be changed each time memory size changes
        mem_size = 4096          # memory pool size in bytes
        memblock_key = 2343      # memory block key, need to keep the same in the ns-3 script
        self.config = config      
        rounds = self.config.fl.rounds
        clients = self.config.clients.total
        ns3settings = {'spokes': clients, 'rounds': rounds}     # Command line arguments for ns3
        self.exp = Experiment(mempool_key, mem_size, 'simple_fed_learning', '../ns-allinone-3.34/ns-3.34')      # Set up the ns-3 environment
        self.exp.reset()                                                                                        # Reset the environment
        self.rl = Ns3AIRL(memblock_key, Array, Act)  
        self.pro = self.exp.run(setting=ns3settings,show_output=True)  
        self.config = config
    
    def access_network(self, client_id):
        latency = 0
        if not self.rl.isFinish():
            with self.rl as data:
                if data != None:
                    #print("a " + str(data.env.env[client_id].datarate))
                    print(str(client_id) + " client: " + str(data.env.env[client_id].latency))
                    latency = data.env.env[client_id].latency #access latency from ns3 simulations
                    #data.act.c = 0
        return latency


    def destroy_network(self):
        #self.pro.wait()
        del self.exp
