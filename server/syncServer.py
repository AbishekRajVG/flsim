import logging
import pickle
import random
import math
from threading import Thread
from server import Server
from .record import Record, Profile
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


class Group(object):
    """Basic async group."""
    def __init__(self, client_list):
        self.clients = client_list

    def set_download_time(self, download_time):
        self.download_time = download_time

    def set_aggregate_time(self):
        """Only run after client configuration"""
        assert (len(self.clients) > 0), "Empty clients in group init!"
        self.delay = max([c.delay for c in self.clients])
        self.aggregate_time = self.download_time + self.delay

        # Get average throughput contributed by this group
        assert (self.clients[0].model_size > 0), "Zero model size in group init!"
        self.throughput = len(self.clients) * self.clients[0].model_size / \
                self.aggregate_time

    def __eq__(self, other):
        return self.aggregate_time == other.aggregate_time

    def __ne__(self, other):
        return self.aggregate_time != other.aggregate_time

    def __lt__(self, other):
        return self.aggregate_time < other.aggregate_time

    def __le__(self, other):
        return self.aggregate_time <= other.aggregate_time

    def __gt__(self, other):
        return self.aggregate_time > other.aggregate_time

    def __ge__(self, other):
        return self.aggregate_time >= other.aggregate_time

class SyncServer(Server):
    """Synchronous federated learning server."""

    def make_clients(self, num_clients):
        super().make_clients(num_clients)

        # Set link speed for clients
        speed = []
        for client in self.clients:
            client.set_link(self.config)
            speed.append(client.speed_mean)

        logging.info('Speed distribution: {} Kbps'.format([s for s in speed]))

        # Initiate client profile of loss and delay
        self.profile = Profile(num_clients)
        self.profile.set_primary_label([client.pref for client in self.clients])

    # Run synchronous federated learning
    def run(self):
        rounds = self.config.fl.rounds
        target_accuracy = self.config.fl.target_accuracy
        reports_path = self.config.paths.reports
        
        mempool_key = 1234 # memory pool key, arbitrary integer large than 1000
        mem_size = 4096                                             # memory pool size in bytes
        memblock_key = 2338                                        # memory block key, need to keep the same in the ns-3 script
        exp = Experiment(mempool_key, mem_size, 'simple_fed_learning', '../ns-allinone-3.34/ns-3.34')      # Set up the ns-3 environment
        #try:
        exp.reset()                                             # Reset the environment
        rl = Ns3AIRL(memblock_key, Env, Act)                    # Link the shared memory block with ns-3 script
        pro = exp.run(show_output=True)    # Set and run the ns-3 script (sim.cc)
        #while not rl.isFinish():
        #    with rl as data:
        #        if data == None:
        #            break
                # AI algorithms here and put tconda activate fl-py37he data back to the action
        #        print("a " + str(data.env.datarate))
        #        print("b " + str(data.env.latency))
        #        data.act.c = 0
            
        #pro.wait()                                              # Wait the ns-3 to stop
        #except Exception as e:
        #    print('Something wrong')
        #    print(e)
        #finally:
        #del exp
        # Init self accuracy records
        self.records = Record()

        if target_accuracy:
            logging.info('Training: {} rounds or {}% accuracy\n'.format(
                rounds, 100 * target_accuracy))
        else:
            logging.info('Training: {} rounds\n'.format(rounds))

        # Perform rounds of federated learning
        T_old = 0.0
        for round in range(1, rounds + 1):
            logging.info('**** Round {}/{} ****'.format(round, rounds))

            # Run the sync federated learning round
            accuracy, T_new = self.sync_round(round, T_old, rl, pro)
            logging.info('Round finished at time {} s\n'.format(T_new))

            # Update time
            T_old = T_new

            # Break loop when target accuracy is met
            if target_accuracy and (accuracy >= target_accuracy):
                logging.info('Target accuracy reached.')
                break

        if reports_path:
            with open(reports_path, 'wb') as f:
                pickle.dump(self.saved_reports, f)
            logging.info('Saved reports: {}'.format(reports_path))
        
        pro.wait()
        del exp

    def sync_round(self, round, T_old, rl, pro):
        import fl_model  # pylint: disable=import-error

        # Select clients to participate in the round
        sample_groups = self.selection()
        sample_clients, throughput = [], []
        for group in sample_groups:
            for client in group.clients:
                client.set_delay()
                sample_clients.append(client)
                throughput.append(client.model_size / client.delay)
            group.set_download_time(T_old)
            group.set_aggregate_time()
        self.throughput = sum([t for t in throughput])

        logging.info('Avg throughput {} kB/s'.format(self.throughput))

        # Configure sample clients
        self.configuration(sample_clients)
        # Use the max delay in all sample clients as the delay in sync round
        #max_delay = max([c.delay for c in sample_clients])
        #print(max_delay)
        max_delay = 0.5
        if not rl.isFinish():
            with rl as data:
                if data != None:
                    # AI algorithms here and put tconda activate fl-py37he data back to the action
                    print("a " + str(data.env.datarate))
                    print("b " + str(data.env.latency))
                    max_delay = data.env.latency
                    data.act.c = 0
        print(max_delay)

        # Run clients using multithreading for better parallelism
        threads = [Thread(target=client.run) for client in sample_clients]
        [t.start() for t in threads]
        [t.join() for t in threads]
        T_cur = T_old + max_delay  # Update current time

        # Receive client updates
        reports = self.reporting(sample_clients)

        # Update profile and plot
        self.update_profile(reports)
        # Plot every plot_interval
        if math.floor(T_cur / self.config.plot_interval) > \
                math.floor(T_old / self.config.plot_interval):
            self.profile.plot(T_cur, self.config.paths.plot)

        # Perform weight aggregation
        logging.info('Aggregating updates')
        updated_weights = self.aggregation(reports)

        # Load updated weights
        fl_model.load_weights(self.model, updated_weights)

        # Extract flattened weights (if applicable)
        if self.config.paths.reports:
            self.save_reports(round, reports)

        # Save updated global model
        self.save_model(self.model, self.config.paths.model)

        # Test global model accuracy
        if self.config.clients.do_test:  # Get average accuracy from client reports
            accuracy = self.accuracy_averaging(reports)
        else:  # Test updated model on server
            testset = self.loader.get_testset()
            batch_size = self.config.fl.batch_size
            testloader = fl_model.get_testloader(testset, batch_size)
            accuracy = fl_model.test(self.model, testloader)

        logging.info('Average accuracy: {:.2f}%'.format(100 * accuracy))
        self.records.append_record(T_cur, accuracy, self.throughput)
        return self.records.get_latest_acc(), self.records.get_latest_t()

    def selection(self):
        # Select devices to participate in round
        clients_per_round = self.config.clients.per_round

        # Select clients randomly
        sample_clients = [client for client in random.sample(
            self.clients, clients_per_round)]

        # In sync case, create one group of all selected clients
        sample_groups = [Group([client for client in sample_clients])]

        return sample_groups

    def update_profile(self, reports):
        for report in reports:
            self.profile.update(report.client_id, report.loss, report.delay,
                                self.flatten_weights(report.weights))
