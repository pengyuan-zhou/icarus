"""Traffic workloads

Every traffic workload to be used with Icarus must be modelled as an iterable
class, i.e. a class with at least an `__init__` method (through which it is
initialized, with values taken from the configuration file) and an `__iter__`
method that is called to return a new event.

Each call to the `__iter__` method must return a 2-tuple in which the first
element is the timestamp at which the event occurs and the second is a
dictionary, describing the event, which must contain at least the three
following attributes:
 * receiver: The name of the node issuing the request
 * content: The name of the content for which the request is issued
 * log: A boolean value indicating whether this request should be logged or not
   for measurement purposes.

Each workload must expose the `contents` attribute which is an iterable of
all content identifiers. This is needed for content placement.
"""
import random
import csv
import array
import math
import networkx as nx

from icarus.tools import TruncatedZipfDist
from icarus.registry import register_workload

__all__ = [
        'DiffrankWorkload'
           ]


@register_workload('DIFFRANK')
class DiffrankWorkload(object):
    #different rankings with same alpha
    def __init__(self, topology,  n_contents, n_rank, rank_per_group, alpha, beta=0, 
            rate=1.0, n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter() 
                if topology.node[v]['stack'][0] == 'receiver']
        self.topology = topology
        rank_lst = array.array('i',(i for i in range(1,(n_rank+1))))
        
        
        #differentiate requests distribution inter groups, each group has $rank_per_group distributions.
        # when num_of_group>N_NODE, multiple groups share a same workload  
        for v in self.receivers:
            g = self.topology.node[v]['group']
            self.topology.node[v]['rank'] = random.choice(array.array('i',(i for i in 
                range(int(rank_per_group*g-rank_per_group+1),int(math.ceil(rank_per_group*g+1)))))) 
        self.n_contents = n_contents
        self.contents_range = int(n_contents * 32)
        self.contents = range(1, self.contents_range + 1)
        self.zipf = TruncatedZipfDist(alpha, self.n_contents)
        self.n_rank = int(n_rank)
        self.alpha = alpha
        self.rate = rate
        self.n_warmup = n_warmup
        self.n_measured = n_measured
        random.seed(seed)
        self.beta = beta
        if beta != 0:
            degree = nx.degree(self.topology)
            self.receivers = sorted(self.receivers, key=lambda x: degree[iter(topology.edge[x]).next()], reverse=True)
            self.receiver_dist = TruncatedZipfDist(beta, len(self.receivers))

    def __iter__(self):
        req_counter = 0
        t_event = 0.0
        while req_counter < self.n_warmup + self.n_measured:
            t_event += (random.expovariate(self.rate))
            if self.beta == 0:
                receiver = random.choice(self.receivers)
            else:
                receiver = self.receivers[self.receiver_dist.rv()-1]
            self.receiver = receiver
            rank_receiver = int(self.topology.node[self.receiver]['rank']-1)
            content = int(self.zipf.rv()) + self.n_contents * rank_receiver
            #print ("content:%d, self.n_contents:%d, rank_receiver:%d") % (content, self.n_contents, rank_receiver)
            log = (req_counter >= self.n_warmup)
            event = {'receiver': receiver, 'content': content, 'log': log}
            yield (t_event, event)
            req_counter += 1
        raise StopIteration()
