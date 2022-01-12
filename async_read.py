import random
from ctypes import *
import socket
import struct
import time
import subprocess

TCP_IP = '127.0.0.1'
TCP_PORT = 8080
PATH='../ns3-fl-network'
PROGRAM='wifi_exp'

class Client:
	def __init__(self, id):
		self.id = id

	def train(self):
		print("Training on client " + str(self.id))


clients = [Client(0), Client(1), Client(2), Client(3), Client(4), Client(5), Client(6),
			Client(7), Client(8), Client(9), Client(10), Client(11), Client(12), Client(13),
			Client(14), Client(15), Client(16), Client(17), Client(18), Client(19)]

def start_ns3():
	proc = subprocess.Popen('./waf build', shell=True, stdout=subprocess.PIPE,
								universal_newlines=True, cwd=PATH)
	proc.wait()
	if proc.returncode != 0:
		exit(-1)

	command = './waf --run "' + PROGRAM + '"'
	print(command)

	proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
							universal_newlines=True, cwd=PATH)

def parse_clients(selected_clients):
	clients_to_send = [0 for _ in range(len(selected_clients))]
	for client in clients:
		clients_to_send[client.id] = 1
	return clients_to_send

def write_socket(selected_clients,s):
	message = struct.pack("II", 1, len(selected_clients))
	s.send(message)
	# for the total number of clients
	# is the index in lit at client.id equal
	for ele in selected_clients:
		s.send(struct.pack("I", ele))

def read_socket(s):
	resp = s.recv(8)
	print("resp")
	print(resp)
	if len(resp) < 8:
		print(len(resp), resp)
	command, nItems = struct.unpack("II", resp)

	print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
	print(command)
	if command == 4:
		return 'end'
	ret = {}
	for i in range(nItems):
		dr = s.recv(8 * 4)
		eid, startTime, endTime, throughput = struct.unpack("Qddd", dr)
		temp = {"startTime": startTime, "endTime": endTime, "throughput": throughput}
		ret[eid] = temp
	return ret

def async_round(s):
	T_old = 0
	agg_time = [T_old] * len(clients)
	#selected_clients = random.seed(clients, 15) #randomly select clients

	#create a map for clients to their ids
	id_to_client = {}

	for client in clients:
		id_to_client[client.id] = (client, T_old)


	to_send = parse_clients(clients)
	write_socket(to_send,s) #send clients to ns-3

	while True:
		simdata = read_socket(s) #check for data in socket

		if simdata != 'end':
			#get the client/group based on the id, use map
			client_id = -1
			for key in simdata:
				client_id = key

			finished_client = id_to_client[client_id][0]
			T_old = id_to_client[client_id][1]

			#train on the client
			finished_client.train() 

			#aggregate time for round 
			T_old += simdata[client_id]["endTime"] - simdata[client_id]["startTime"]
			id_to_client[client_id] = (finished_client, T_old)

			#update T_old for that group, most recent T_old should be latest round time
			T_new = T_old
			print("Finish training on client " + str(client_id) + " at " + str(T_new))

		elif simdata == 'end':
			break

	print("Round finished at " + str(T_new))

def run():
	start_ns3()
	time.sleep(2)
	s = socket.create_connection((TCP_IP, TCP_PORT,))
	async_round(s)
	s.close()

run()


