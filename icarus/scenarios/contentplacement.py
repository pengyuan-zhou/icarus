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
def get_sources(topology):
    return [v for v in topology if topology.node[v]['stack'][0] == 'source']


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
    sourcelist = get_sources(topology)
    sourcelist.sort()
    sourcelistas = [None] * len(asns)
    # divide source nodes by AS
    sourcelistas = [[j for j in sourcelist if ('S%d' % i) in j] for i in range(len(asns))]
   
    content_placement = collections.defaultdict(set)
    # problem1. how to divide content set according to user number of AS, which is more realistic, now is cut evenly
    # problem2, how to let users within each AS send request following majorly the set distribution, to make it make sense.
    # logic of placement: at least includes: 1. share intra AS 2. share inter AS
    # first divide global content set into each AS, with static overlap ratio, resulting in
    # some ASes have smaller while others have bigger overlap
    # then divide content set of each AS into each Publisher, follow the same way
    # overlap(OL) intra AS, OL_inter_AS
    ola=0.4#overlap of publishers intra AS
    ole=0.2#overlap of content sets inter AS
    #sizeAS * len(asns) - sizeAS * ole * (len(asns)-1) = len(contents)
    sizeAS = len(content)/(len(asns) - ole*(len(asns)-1)) # size of content set of each AS
    sizeP_ASi = sizeAS/(len(sourcelistas[i]) - ola*(len(sourcelistas[i])-1))#size of content set of each publisher
    size = int(len(contents)/numSource) #source in diff ASes have same contents,which doesn't influence since we block inter AS transfer by defining largeinter AS delay
    print ("each source node have %d content" % size)
    source_nodes = sorted(source_nodes)
    #we define different zize of publishers(number of connected ASes)
    #through combining source nodes, i.e., if let src_AS0_0 store the
    #same content set with src_AS0_0, then they are one publisher
    #that can let us define different publishers connected with different ASes.
    v=0
    while v < len(source_nodes):
        #the last source node will have slide more contents than others, to cover all the contents in the global set
        # only for when signing eaualing number of nodes
        i = 0
        while i < numSource: 
            if (i == numSource-1):
                for c in contents[(size*i):]:
                    content_placement[source_nodes[v]].add(c)
            else:
                for c in contents[size*i:size*(i+1)]:
                    content_placement[source_nodes[v]].add(c)
            i += 1 
            v += 1
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
