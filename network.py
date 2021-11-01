from py_interface import *
from ctypes import *

# The environment (in this example, contain 'a' and 'b')
# shared between ns-3 and python with the same shared memory
# using the ns3-ai model.
class Env(Structure):
    _pack_ = 1
    _fields_ = [
        ('datarate', c_double),
        ('latency', c_double),
    ]

# The result (in this example, contain 'c') calculated by python
# and put back to ns-3 with the shared memory.
class Act(Structure):
    _pack_ = 1
    _fields_ = [
        ('c', c_double)
    ]

class Network(object):
    def __init__(self):
        mempool_key = 1234                                                                                 # memory pool key, arbitrary integer large than 1000
        mem_size = 4096                                                                                    # memory pool size in bytes
        memblock_key = 2338                                                                                # memory block key, need to keep the same in the ns-3 script
        self.exp = Experiment(mempool_key, mem_size, 'simple_fed_learning', '../ns-allinone-3.34/ns-3.34')      # Set up the ns-3 environment
        self.exp.reset()                                                                                        # Reset the environment
        self.rl = Ns3AIRL(memblock_key, Env, Act)    
        self.pro = self.exp.run(show_output=True)  

    def access_network(self):
        latency = 0
        if not self.rl.isFinish():
            with self.rl as data:
                if data != None:
                    # AI algorithms here and put tconda activate fl-py37he data back to the action
                    print("a " + str(data.env.datarate))
                    print("b " + str(data.env.latency))
                    latency = data.env.latency
                    data.act.c = 0
        return latency


    def destroy_network(self):
        #self.pro.wait()
        del self.exp
