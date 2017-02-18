"""
    workload used to get each server with same interest users
    so that can provide request file to identify the accuracy of clustering 
    
    
    Traffic workloads

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

import networkx as nx

from collections import OrderedDict

from random import randint
from icarus.tools import TruncatedZipfDist
from icarus.registry import register_workload

__all__ = [
		'AllsameWorkload',
        'DiffalphaWorkload',
        'GroupdiffalphaWorkload',
		'DiffrankWorkload',
		'GroupdiffrankWorkload',
        'AlldiffWorkload',
        'GroupalldiffrankWorkload',
        'GroupalldiffWorkload',
        'GlobalzipfWorkload',
        'LocalzipfWorkload',
        'Groupalldiff1Workload',
        'GroupzipfWorkload',
        'GlobetraffWorkload',
        'TraceDrivenWorkload'
           ]



@register_workload('ALLSAME')
class AllsameWorkload(object):
    #same rankings with same alpha
    def __init__(self, topology, diff, rank_diff, n_contents, group_of_user, alpha, beta=0, rate=1.0, n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter()
        			if topology.node[v]['stack'][0] == 'receiver']
        self.zipf = TruncatedZipfDist(alpha, n_contents)
        self.n_contents = n_contents
        self.contents = range(1, n_contents + 1)
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
            content = int(self.zipf.rv())
            log = (req_counter >= self.n_warmup)
            event = {'receiver': receiver, 'content': content, 'log': log}
            yield (t_event, event)
            req_counter += 1
        raise StopIteration()



@register_workload('DIFFALPHA')
class DiffalphaWorkload(object):
    #different rankings with same alpha
    def __init__(self, topology, diff, rank_diff, n_contents, rank_sum, group_of_user, alpha, beta=0, rate=1.0, n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter() if topology.node[v]['stack'][0] == 'receiver']
        self.diff = diff
        self.topology = topology
        self.zipfset = []
        
        self.zipfset.append(TruncatedZipfDist(alpha-self.diff, n_contents))
        self.zipfset.append(TruncatedZipfDist(alpha, n_contents))
        self.zipfset.append(TruncatedZipfDist(alpha+self.diff, n_contents))
        for v in self.receivers:
            alpha_choose = randint(0,2)
            self.topology.node[v]['zipf'] = alpha_choose
            positive_choose = randint(0, 1)
            self.topology.node[v]['positive'] = positive_choose
        self.n_contents = n_contents
        self.contents_range = n_contents
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
            alpha_receiver = self.topology.node[self.receiver]['zipf']
            self.zipf = self.zipfset[alpha_receiver]
            positive_receiver = self.topology.node[self.receiver]['positive']
            content = int((-1)**positive_receiver * (int(self.zipf.rv())-positive_receiver*(self.n_contents+1)))
            if content>(self.n_contents + 1) or content <1:
                print positive_receiver,content
            log = (req_counter >= self.n_warmup)
            event = {'receiver': receiver, 'content': content, 'log': log}
            yield (t_event, event)
            req_counter += 1
        raise StopIteration()




@register_workload('GROUPDIFFALPHA')
class GroupdiffalphaWorkload(object):
    #different rankings with same alpha
    def __init__(self, topology, diff, rank_diff, n_contents, rank_sum, group_of_user, alpha, beta=0, rate=1.0, n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter() if topology.node[v]['stack'][0] == 'receiver']
        self.diff = diff
        self.topology = topology
        self.zipfset = []
        
        self.zipfset.append(TruncatedZipfDist(alpha-self.diff, n_contents))
        self.zipfset.append(TruncatedZipfDist(alpha, n_contents))
        self.zipfset.append(TruncatedZipfDist(alpha+self.diff, n_contents))
        for v in self.receivers:
            group_v = self.topology.node[v]['group']
            alpha_choose = group_v % len(self.zipfset)
            self.topology.node[v]['zipf'] = alpha_choose
            positive_choose = group_v % 2
            self.topology.node[v]['positive'] = positive_choose
        self.n_contents = n_contents
        self.contents_range = n_contents
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
            alpha_receiver = self.topology.node[self.receiver]['zipf']
            self.zipf = self.zipfset[alpha_receiver]
            positive_receiver = self.topology.node[self.receiver]['positive']
            content = int((-1)**positive_receiver * (int(self.zipf.rv())-positive_receiver*(self.n_contents+1)))
            #print positive_receiver,(-1)**positive_receiver
            log = (req_counter >= self.n_warmup)
            event = {'receiver': receiver, 'content': content, 'log': log}
            yield (t_event, event)
            req_counter += 1
        raise StopIteration()

@register_workload('DIFFRANK')
class DiffrankWorkload(object):
    #different rankings with same alpha
    def __init__(self, topology, diff, rank_diff, n_contents, rank_sum, group_of_user, alpha, beta=0, rate=1.0, n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter() if topology.node[v]['stack'][0] == 'receiver']
        self.diff = diff
        self.topology = topology
        rank_choose = 0

        #different areas have different rankings, but all users have same alpha choices
        for v in self.receivers:
            rank_choose = randint(0, rank_sum-1)
            #rank_set[rank_choose].append(v)
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



@register_workload('GROUPDIFFRANK')
class GroupdiffrankWorkload(object):
    #different rankings with different alpha
    def __init__(self, topology, diff, rank_diff, n_contents, rank_sum, group_of_user, alpha, beta=0, rate=1.0, n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter()
        			if topology.node[v]['stack'][0] == 'receiver']
        self.group_of_user = group_of_user
        OrderedDict(sorted(self.group_of_user.items(), key=lambda t: t[0]))
        self.zipf = TruncatedZipfDist(alpha, n_contents)
        self.diff = diff
        self.topology = topology
        rank_choose = 0
        
        #different areas have different rankings, but all users have same alpha choices
        for i in self.receivers:
            for k, v in self.group_of_user.items():
                if i in v:
                    key_receiver = k
                    break
            key_i = self.group_of_user.keys().index(key_receiver)
            rank_choose = key_i % rank_sum
            #rank_set[rank_choose].append(v)
            self.topology.node[i]['rank'] = rank_choose
            #print i, key_i, rank_choose
        
        with open('%s.csv' % ('user_groupdiffrank'+str(rank_sum)), 'a+') as f:
            for k, v in self.group_of_user.items():
                for i in v:
                    rank_choose = self.topology.node[i]['rank']
                    user_interest = "%s,%s" % (i, rank_choose)
                    f.seek(0)
                    f.write(user_interest)
                    f.write("\n")
        
        self.n_contents = n_contents
        self.contents_range = int(n_contents * (1 + rank_diff * (rank_sum - 1)))
        self.contents = range(1, self.contents_range + 1)
        self.rank_diff = rank_diff
        self.alpha = alpha
        self.zipf = TruncatedZipfDist(alpha, self.n_contents)
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
        with open('%s.csv' % ('user_content_groupdiffrank'+str(self.rank_sum)), 'a+') as f:
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
                if req_counter >= self.n_warmup:
                    event_print = "%s,%s" % (receiver, content)
                    f.seek(0)
                    f.write(event_print)
                    f.write("\n")
                #print event
                yield (t_event, event)
                req_counter += 1
            raise StopIteration()



@register_workload('ALLDIFF')
class AlldiffWorkload(object):
    #different rankings with different alphas
    def __init__(self, topology, diff, rank_diff, n_contents, rank_sum, alpha, beta=0, rate=1.0,
                 n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter() if topology.node[v]['stack'][0] == 'receiver']
        self.diff = diff
        self.topology = topology
        self.zipfset = []
        #self.alpha_set = [alpha-diff, alpha, alpha+diff]
        alpha_choose = alpha
        rank_choose = 0
        self.zipfset.append(TruncatedZipfDist(alpha-self.diff, n_contents))
        self.zipfset.append(TruncatedZipfDist(alpha, n_contents))
        self.zipfset.append(TruncatedZipfDist(alpha+self.diff, n_contents))
        #different areas have different rankings, but all users have same alpha choices
        for v in self.receivers:
            alpha_choose = randint(0,2)
            self.topology.node[v]['zipf'] = alpha_choose
            rank_choose = randint(0, rank_sum-1)
            #rank_set[rank_choose].append(v)
            self.topology.node[v]['rank'] = rank_choose
        self.n_contents = n_contents
        self.contents_range = int(n_contents * (1 + rank_diff * (rank_sum - 1)))
        self.contents = range(1, self.contents_range + 1)
        self.rank_diff = rank_diff
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
            alpha_receiver = self.topology.node[self.receiver]['zipf']
            self.zipf = self.zipfset[alpha_receiver]
            rank_receiver = self.topology.node[self.receiver]['rank']
            content = int(self.zipf.rv()) + self.n_contents * self.rank_diff * rank_receiver
            #print receiver, alpha_receiver, rank_receiver, content 
            log = (req_counter >= self.n_warmup)
            event = {'receiver': receiver, 'content': content, 'log': log}
            yield (t_event, event)
            req_counter += 1
        raise StopIteration()



@register_workload('GROUPALLDIFFRANK')
class GroupalldiffrankWorkload(object):
    #different rankings with different alpha
    def __init__(self, topology, diff, rank_diff, n_contents, rank_sum, group_of_user, alpha, beta=0, rate=1.0,
                 n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter()
        			if topology.node[v]['stack'][0] == 'receiver']
        self.group_of_user = group_of_user
        OrderedDict(sorted(self.group_of_user.items(), key=lambda t: t[0]))
        self.diff = diff
        self.topology = topology
        self.zipfset = []
        #self.alpha_set = [alpha-diff, alpha, alpha+diff]
        alpha_choose = alpha
        rank_choose = 0
        self.zipfset.append(TruncatedZipfDist(alpha-self.diff, n_contents))
        self.zipfset.append(TruncatedZipfDist(alpha, n_contents))
        self.zipfset.append(TruncatedZipfDist(alpha+self.diff, n_contents))
        #different areas have different rankings, but all users have same alpha choices
        for i in self.receivers:
            alpha_choose = randint(0,2)
            self.topology.node[i]['zipf'] = alpha_choose
            for k, v in self.group_of_user.items():
                if i in v:
                    key_receiver = k
                    break
            key_i = self.group_of_user.keys().index(key_receiver)
            rank_choose = key_i % rank_sum
            self.topology.node[i]['rank'] = rank_choose
        self.n_contents = n_contents
        self.contents_range = int(n_contents * (1 + rank_diff * (rank_sum - 1)))
        self.contents = range(1, self.contents_range + 1)
        self.rank_diff = rank_diff
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
            alpha_receiver = self.topology.node[self.receiver]['zipf']
            self.zipf = self.zipfset[alpha_receiver]
            rank_receiver = self.topology.node[self.receiver]['rank']
            content = int(self.zipf.rv()) + self.n_contents * self.rank_diff * rank_receiver
            #print receiver, alpha_receiver, rank_receiver, content
            log = (req_counter >= self.n_warmup)
            event = {'receiver': receiver, 'content': content, 'log': log}
            yield (t_event, event)
            req_counter += 1
        raise StopIteration()


@register_workload('GROUPALLDIFF')
class GroupalldiffWorkload(object):
    #different rankings with different alpha
    def __init__(self, topology, diff, rank_diff, n_contents, rank_sum, group_of_user, alpha, beta=0, rate=1.0,
                 n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter()
        			if topology.node[v]['stack'][0] == 'receiver']
        self.group_of_user = group_of_user
        OrderedDict(sorted(self.group_of_user.items(), key=lambda t: t[0]))
        self.diff = diff
        self.topology = topology
        self.zipfset = []
        #self.alpha_set = [alpha-diff, alpha, alpha+diff]
        alpha_choose = alpha
        rank_choose = 0
        self.zipfset.append(TruncatedZipfDist(alpha-self.diff, n_contents))
        self.zipfset.append(TruncatedZipfDist(alpha, n_contents))
        self.zipfset.append(TruncatedZipfDist(alpha+self.diff, n_contents))
        #different areas have different rankings, but all users have same alpha choices
        for i in self.receivers:
            for k, v in self.group_of_user.items():
                if i in v:
                    key_receiver = k
                    break
            key_i = self.group_of_user.keys().index(key_receiver)
            alpha_choose = key_i % len(self.zipfset)
            self.topology.node[i]['zipf'] = alpha_choose
            rank_choose = key_i % rank_sum
            #rank_set[rank_choose].append(v)
            self.topology.node[i]['rank'] = rank_choose
        self.n_contents = n_contents
        self.contents_range = int(n_contents * (1 + rank_diff * (rank_sum - 1)))
        self.contents = range(1, self.contents_range + 1)
        self.rank_diff = rank_diff
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
            alpha_receiver = self.topology.node[self.receiver]['zipf']
            self.zipf = self.zipfset[alpha_receiver]
            rank_receiver = self.topology.node[self.receiver]['rank']
            content = int(self.zipf.rv()) + self.n_contents * self.rank_diff * rank_receiver
            log = (req_counter >= self.n_warmup)
            event = {'receiver': receiver, 'content': content, 'log': log}
            #print event
            yield (t_event, event)
            req_counter += 1
        raise StopIteration()


@register_workload('GLOBALZIPF')
class GlobalzipfWorkload(object):
    #different alphas, randomly choose one of them
    def __init__(self, topology, diff, n_contents, group_of_user, alpha, beta=0, rate=1.0,
                 n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter()
        			if topology.node[v]['stack'][0] == 'receiver']
        self.diff = diff
        self.topology = topology
        self.zipfset = []
        zipf_i = 0
        self.group_of_user = group_of_user
        OrderedDict(sorted(self.group_of_user.items(), key=lambda t: t[0]))
        while (zipf_i < len(self.group_of_user)):
            self.zipfset.append(TruncatedZipfDist(alpha+self.diff*zipf_i, n_contents))
            zipf_i +=1

        self.n_contents = n_contents
        self.contents = range(1, n_contents + 1)
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
            if 'zipf' not in self.topology.node[self.receiver]:
                self.zipf = random.choice(self.zipfset)
                self.topology.node[self.receiver]['zipf'] = self.zipfset.index(self.zipf)
            else:
                self.zipf = self.zipfset[self.topology.node[self.receiver]['zipf']]
            content = int(self.zipf.rv())
            log = (req_counter >= self.n_warmup)
            event = {'receiver': receiver, 'content': content, 'log': log}
            yield (t_event, event)
            req_counter += 1
        raise StopIteration()



@register_workload('LOCALZIPF')
class LocalzipfWorkload(object):
    #each local users choose from a part of zipfset
    def __init__(self, topology, diff, n_contents, group_of_user, alpha, beta=0, rate=1.0,
                 n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter()
                	if topology.node[v]['stack'][0] == 'receiver']
        self.diff = diff
        self.topology = topology
        self.zipfset = []
        zipf_i = 0
        self.group_of_user = group_of_user
        OrderedDict(sorted(self.group_of_user.items(), key=lambda t: t[0]))

        while (zipf_i < len(self.group_of_user)):
            self.zipfset.append(TruncatedZipfDist(alpha+self.diff*zipf_i, n_contents))
            zipf_i +=1
        self.n_contents = n_contents
        self.contents = range(1, n_contents + 1)
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
            #the key of edge cache which the receiver belongs to
            key_receiver = 0
            #the index of the key which the receiver belongs to
            key_i = 0
	    	#the index of zipf of receiver
            i_of_zipf = 0
            #the max index in zipfset
            upper = 0
            a = b = c = 0
            self.receiver = receiver
            if 'zipf' not in self.topology.node[self.receiver]:
                for k, v in self.group_of_user.items():
                	if self.receiver in v:
                   		key_receiver = k
                   		break
            	key_i = self.group_of_user.keys().index(key_receiver)
            	upper = len(self.group_of_user)-1
            	#give three choices for receiver to choose a zipf randomly, narrowing down to a part of the selections
            	a = key_i*key_i
            	b = key_i*(key_i+1)
            	c = key_i*(key_i+2)
            	i_of_zipf = random.choice([a%upper, b%upper, c%upper])
            	self.zipf = self.zipfset[i_of_zipf]
                self.topology.node[self.receiver]['zipf'] = i_of_zipf
            else:
                self.zipf = self.zipfset[self.topology.node[self.receiver]['zipf']]
            
            content = int(self.zipf.rv())
            log = (req_counter >= self.n_warmup)
            event = {'receiver': receiver, 'content': content, 'log': log}
            yield (t_event, event)
            req_counter += 1
        raise StopIteration()


@register_workload('GROUPALLDIFF1')
class Groupalldiff1Workload(object):
    #different rankings with different alpha
    def __init__(self, topology, diff, n_contents, group_of_user, alpha, beta=0, rate=1.0,
                    n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter()
                	if topology.node[v]['stack'][0] == 'receiver']
        self.diff = diff
        self.topology = topology
        self.zipfset = []
        zipf_i = 0
        self.group_of_user = group_of_user
        OrderedDict(sorted(self.group_of_user.items(), key=lambda t: t[0]))
        while (zipf_i < len(self.group_of_user)):
            self.zipfset.append(TruncatedZipfDist(alpha+self.diff*zipf_i, n_contents))
            zipf_i +=1

        self.n_contents = n_contents * len(self.zipfset)
        self.contents = range(1, self.n_contents + 1)
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
            # the key of the edge cache connecting to the receiver
            key_receiver = 0
            # the index of the key
            key_i = 0
            self.receiver = receiver
            if 'zipf' not in self.topology.node[self.receiver]:
            	for k, v in self.group_of_user.items():
                    if receiver in v:
                    	key_receiver = k
                    	break

            	key_i = self.group_of_user.keys().index(key_receiver)
            	self.zipf = self.zipfset[key_i]
                self.topology.node[self.receiver]['zipf'] = key_i
            else:
                self.zipf = self.zipfset[self.topology.node[self.receiver]['zipf']]
     
            content = int(self.zipf.rv()) + self.n_contents / len(self.zipfset) * key_i
            log = (req_counter >= self.n_warmup)
            event = {'receiver': receiver, 'content': content, 'log': log}
            yield (t_event, event)
            req_counter += 1
        raise StopIteration()
        
@register_workload('GROUPZIPF')
class GroupzipfWorkload(object):
    #different rankings with different alpha
    def __init__(self, topology, diff, n_contents, group_of_user, alpha, beta=0, rate=1.0,
                    n_warmup=10**5, n_measured=4*10**5, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter()
                	if topology.node[v]['stack'][0] == 'receiver']
        self.diff = diff
        self.topology = topology 
        self.zipfset = []
        zipf_i = 0
        self.group_of_user = group_of_user
        OrderedDict(sorted(self.group_of_user.items(), key=lambda t: t[0]))
        while (zipf_i < len(self.group_of_user)):
            self.zipfset.append(TruncatedZipfDist(alpha+self.diff*zipf_i, n_contents))
            zipf_i +=1
            
        self.n_contents = n_contents 
        self.contents = range(1, self.n_contents + 1)
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
            # the key of the edge cache connecting to the receiver
            key_receiver = 0
            # the index of the key
            key_i = 0
            self.receiver = receiver
            if 'zipf' not in self.topology.node[self.receiver]:
                for k, v in self.group_of_user.items():
                    if receiver in v:
                        key_receiver = k
                        break

                key_i = self.group_of_user.keys().index(key_receiver)
                self.zipf = self.zipfset[key_i]
                self.topology.node[self.receiver]['zipf'] = key_i
            else:
                self.zipf = self.zipfset[self.topology.node[self.receiver]['zipf']]
            content = int(self.zipf.rv())
            log = (req_counter >= self.n_warmup)
            event = {'receiver': receiver, 'content': content, 'log': log}
            yield (t_event, event)
            req_counter += 1
        raise StopIteration()





@register_workload('GLOBETRAFF')
class GlobetraffWorkload(object):
    """Parse requests from GlobeTraff workload generator
    
    All requests are mapped to receivers uniformly unless a positive *beta*
    parameter is specified.
    
    If a *beta* parameter is specified, then receivers issue requests at
    different rates. The algorithm used to determine the requests rates for 
    each receiver is the following:
     * All receiver are sorted in decreasing order of degree of the PoP they
       are attached to. This assumes that all receivers have degree = 1 and are
       attached to a node with degree > 1
     * Rates are then assigned following a Zipf distribution of coefficient
       beta where nodes with higher-degree PoPs have a higher request rate 
    
    Parameters
    ----------
    topology : fnss.Topology
        The topology to which the workload refers
    reqs_file : str
        The GlobeTraff request file
    contents_file : str
        The GlobeTraff content file
    beta : float, optional
        Spatial skewness of requests rates
        
    Returns
    -------
    events : iterator
        Iterator of events. Each event is a 2-tuple where the first element is
        the timestamp at which the event occurs and the second element is a
        dictionary of event attributes.
    """
    
    def __init__(self, topology, reqs_file, contents_file, beta=0, **kwargs):
        """Constructor"""
        if beta < 0:
            raise ValueError('beta must be positive')
        self.receivers = [v for v in topology.nodes_iter() 
                     if topology.node[v]['stack'][0] == 'receiver']
        self.n_contents = 0
        with open(contents_file, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            for content, popularity, size, app_type in reader:
                self.n_contents = max(self.n_contents, content)
        self.n_contents += 1
        self.contents = range(self.n_contents)
        self.request_file = reqs_file
        self.beta = beta
        if beta != 0:
            degree = nx.degree(self.topology)
            self.receivers = sorted(self.receivers, key=lambda x: 
                                    degree[iter(topology.edge[x]).next()], 
                                    reverse=True)
            self.receiver_dist = TruncatedZipfDist(beta, len(self.receivers))
        
    def __iter__(self):
        with open(self.request_file, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            for timestamp, content, size in reader:
                if self.beta == 0:
                    receiver = random.choice(self.receivers)
                else:
                    receiver = self.receivers[self.receiver_dist.rv()-1]
                event = {'receiver': receiver, 'content': content, 'size': size}
                yield (timestamp, event)
        raise StopIteration()

@register_workload('TRACE_DRIVEN')
class TraceDrivenWorkload(object):
    """Parse requests from a generic request trace.
    
    This workload requires two text files:
     * a requests file, where each line corresponds to a string identifying
       the content requested
     * a contents file, which lists all unique content identifiers appearing
       in the requests file.
       
    Since the trace do not provide timestamps, requests are scheduled according
    to a Poisson process of rate *rate*. All requests are mapped to receivers
    uniformly unless a positive *beta* parameter is specified.
    
    If a *beta* parameter is specified, then receivers issue requests at
    different rates. The algorithm used to determine the requests rates for 
    each receiver is the following:
     * All receiver are sorted in decreasing order of degree of the PoP they
       are attached to. This assumes that all receivers have degree = 1 and are
       attached to a node with degree > 1
     * Rates are then assigned following a Zipf distribution of coefficient
       beta where nodes with higher-degree PoPs have a higher request rate 
        
    Parameters
    ----------
    topology : fnss.Topology
        The topology to which the workload refers
    reqs_file : str
        The path to the requests file
    contents_file : str
        The path to the contents file
    n_contents : int
        The number of content object (i.e. the number of lines of contents_file)
    n_warmup : int
        The number of warmup requests (i.e. requests executed to fill cache but
        not logged)
    n_measured : int
        The number of logged requests after the warmup
    rate : float, optional
        The network-wide mean rate of requests per second
    beta : float, optional
        Spatial skewness of requests rates
        
    Returns
    -------
    events : iterator
        Iterator of events. Each event is a 2-tuple where the first element is
        the timestamp at which the event occurs and the second element is a
        dictionary of event attributes.
    """
    
    def __init__(self, topology, reqs_file, contents_file, n_contents,
                 n_warmup, n_measured, rate=1.0, beta=0, **kwargs):
        """Constructor"""
        if beta < 0:
            raise ValueError('beta must be positive')
        # Set high buffering to avoid one-line reads
        self.buffering = 64*1024*1024
        self.n_contents = n_contents
        self.n_warmup = n_warmup
        self.n_measured = n_measured
        self.reqs_file = reqs_file
        self.rate = rate
        self.receivers = [v for v in topology.nodes_iter() 
                          if topology.node[v]['stack'][0] == 'receiver']
        self.contents = []
        with open(contents_file, 'r', buffering=self.buffering) as f:
            for content in f:
                self.contents.append(content)
        self.beta = beta
        if beta != 0:
            degree = nx.degree(topology)
            self.receivers = sorted(self.receivers, key=lambda x:
                                    degree[iter(topology.edge[x]).next()],
                                    reverse=True)
            self.receiver_dist = TruncatedZipfDist(beta, len(self.receivers))
        
    def __iter__(self):
        req_counter = 0
        t_event = 0.0
        with open(self.reqs_file, 'r', buffering=self.buffering) as f:
            for content in f:
                t_event += (random.expovariate(self.rate))
                if self.beta == 0:
                    receiver = random.choice(self.receivers)
                else:
                    receiver = self.receivers[self.receiver_dist.rv()-1]
                log = (req_counter >= self.n_warmup)
                event = {'receiver': receiver, 'content': content, 'log': log}
                yield (t_event, event)
                req_counter += 1
                if(req_counter >= self.n_warmup + self.n_measured):
                    raise StopIteration()
            raise ValueError("Trace did not contain enough requests")
