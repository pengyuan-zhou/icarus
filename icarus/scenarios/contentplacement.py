"""Content placement strategies.

This module contains function to decide the allocation of content objects to
source nodes.
"""
import random
import collections

from fnss.util import random_from_pdf
from icarus.registry import register_content_placement


__all__ = ['ases_content_placement','uniform_content_placement', 'weighted_content_placement']


def apply_content_placement(placement, topology):
    """Apply a placement to a topology

    Parameters
    ----------
    placement : dict of sets
        Set of contents to be assigned to nodes keyed by node identifier
    topology : Topology
        The topology
    """
    for v, contents in placement.items():
        topology.node[v]['stack'][1]['contents'] = contents
        print (v,len(contents))
def get_sources(topology):
    return [v for v in topology if topology.node[v]['stack'][0] == 'source']

def get_receivers(topology):
    return [v for v in topology if topology.node[v]['stack'][0] == 'receiver']

@register_content_placement('ASES')
def ases_content_placement(topology, asns, rank_sum, contents, seed=None):
    """Places content sets to source nodes randomly following a uniform
    distribution.

    Parameters
    ----------
    topology : Topology
        The topology object
   contents : iterable
        Iterable of content objects
    source_nodes : list
        List of nodes of the topology which are content sources

    Returns
    -------
    cache_placement : dict
        Dictionary mapping content objects to source nodes

    Notes
    -----
    A deterministic placement of objects (e.g., for reproducing results) can be
    achieved by using a fix seed value
    """
    random.seed(seed)
    receiverlist = get_receivers(topology)
    receiverlist.sort()
    receiverlistas = [None] * len(asns)
    receiverlistas = [[j for j in receiverlist if ('S%d' % i) in j] for i in range(len(asns))]
    numReceiver = sum(len(receiver) for receiver in receiverlistas) 
    sourcelist = get_sources(topology)
    sourcelist.sort()
    sourcelistas = [None] * len(asns)
    # divide source nodes by AS
    sourcelistas = [[j for j in sourcelist if ('S%d' % i) in j] for i in range(len(asns))]
    numSource = sum(len(source) for source in sourcelistas) 
    content_placement = collections.defaultdict(set)
    # problem1.solved, because number of source node which is proportional to AS size, is also proportional to nubmer of users
    # problem2, how to let users within each AS send request following majorly the set distribution, to make it make sense.
    # logic of placement: at least includes: 1. share intra AS 2. share inter AS
    # first divide global content set into each AS, with static overlap ratio, resulting in
    # some ASes have smaller while others have bigger overlap
    # then divide content set of each AS into each Publisher, follow the same way
    # assign content placement accroding to size of AS, e.g., number of source nodes.
    size_AS = [None] * len(asns)
    for i in range(len(asns)):
        if i < len(asns)-1 :
            size_AS[i] = int(len(contents) * len(receiverlistas[i])/numReceiver) #use number of receiver as proportion, because need to define same number of source nodes in each AS
        else:
            size_AS[i] = len(contents) - sum(size_AS[:i])
    #content set of each AS
    content_AS = [None] * len(asns)
    for i in range(len(asns)):
        if i == 0:
            content_AS[i] = contents[0:size_AS[i]]
        elif i == len(asns)-1 :
            content_AS[i] = contents[sum(size_AS[:i]):] 
        else:
            content_AS[i] = contents[sum(size_AS[:i]):sum(size_AS[:i+1])] 
    #source_nodes = sorted(source_nodes)
    #we define different zize of publishers(number of connected ASes)
    #through combining source nodes, i.e., if let src_AS0_0 store the
    #same content set with src_AS0_0, then they are one publisher
    #that can let us define different publishers connected with different ASes.
    for source in sourcelistas:
        size = size_AS[sourcelistas.index(source)]/len(source)
        i=0
        while i < len(source):
            if i == (len(source)-1):
                for c in content_AS[sourcelistas.index(source)][(size*i):]:
                    content_placement[source[i]].add(c)
            else:
                for c in content_AS[sourcelistas.index(source)][size*i:size*(i+1)]:
                    content_placement[source[i]].add(c)
            i+=1
 
    apply_content_placement(content_placement, topology)
    
    
@register_content_placement('UNIFORM')
def uniform_content_placement(topology, contents, seed=None):
    """Places content objects to source nodes randomly following a uniform
    distribution.
    Parameters
    ----------
    topology : Topology
        The topology object
   contents : iterable
        Iterable of content objects
    source_nodes : list
        List of nodes of the topology which are content sources
    Returns
    -------
    cache_placement : dict
        Dictionary mapping content objects to source nodes
    Notes
    -----
    A deterministic placement of objects (e.g., for reproducing results) can be
    achieved by using a fix seed value
    """
    random.seed(seed)
    source_nodes = get_sources(topology)
    content_placement = collections.defaultdict(set)
    for c in contents:
        content_placement[random.choice(source_nodes)].add(c)
    apply_content_placement(content_placement, topology)

    
@register_content_placement('WEIGHTED')
def weighted_content_placement(topology, contents, source_weights, seed=None):
    """Places content objects to source nodes randomly according to the weight
    of the source node.

    Parameters
    ----------
    topology : Topology
        The topology object
   contents : iterable
        Iterable of content objects
    source_weights : dict
        Dict mapping nodes nodes of the topology which are content sources and
        the weight according to which content placement decision is made.

    Returns
    -------
    cache_placement : dict
        Dictionary mapping content objects to source nodes

    Notes
    -----
    A deterministic placement of objects (e.g., for reproducing results) can be
    achieved by using a fix seed value
    """
    random.seed(seed)
    norm_factor = float(sum(source_weights.values()))
    source_pdf = dict((k, v / norm_factor) for k, v in source_weights.items())
    content_placement = collections.defaultdict(set)
    for c in contents:
        content_placement[random_from_pdf(source_pdf)].add(c)
    apply_content_placement(content_placement, topology)
