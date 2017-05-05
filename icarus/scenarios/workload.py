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

from random import random as rm
from bisect import bisect
from icarus.tools import TruncatedZipfDist
from icarus.registry import register_workload

__all__ = [
        'DiffrankWorkload'
           ]


@register_workload('DIFFRANK')
class DiffrankWorkload(object):
    #different rankings with same alpha
    def __init__(self, topology, asns, diff, rank_diff, n_contents, rank_sum, alpha, beta=0, rate=1.0, n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter() if topology.node[v]['stack'][0] == 'receiver']
        self.diff = diff
        self.topology = topology
        rank_choose = 0
        #request distributions are uniform distributed to users
        ranks = [i for i in range(rank_sum)]
        #uniform distribution of request patterns
        weights= [float(1.0/rank_sum)] * rank_sum
        for v in self.receivers:
            rank_choose = weighted_choice(ranks, weights)
            self.topology.node[v]['rank'] = rank_choose
        self.n_contents = n_contents
        self.contents_range = int(n_contents * (1 + rank_diff * (rank_sum - 1)))
        self.contents = range(1, self.contents_range + 1)
        self.zipf = TruncatedZipfDist(alpha, self.n_contents)
        self.rank_diff = rank_diff
        self.rank_sum = rank_sum
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
            rank_receiver = self.topology.node[self.receiver]['rank']
            content = int(self.zipf.rv()) + self.n_contents * self.rank_diff * rank_receiver
            log = (req_counter >= self.n_warmup)
            event = {'receiver': receiver, 'content': content, 'log': log}
            yield (t_event, event)
            req_counter += 1
        raise StopIteration()

      
def weighted_choice(values, weights):
    total = 0
    cum_weights = []
    for w in weights:
        total += w
        cum_weights.append(total)
    x = rm() * total
    i = bisect(cum_weights, x)
    return values[i]
