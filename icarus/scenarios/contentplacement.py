"""Content placement strategies.

This module contains function to decide the allocation of content objects to
source nodes.
"""
import random
import collections

from fnss.util import random_from_pdf
from icarus.registry import register_content_placement


__all__ = ['uniform_content_placement', 'weighted_content_placement']


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

@register_content_placement('UNIFORM')
def uniform_content_placement(topology, rank_sum, contents, seed=None):
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
    source_nodes = get_sources(topology)
    content_placement = collections.defaultdict(set)
    #assuming each source node as a publisher, size_set is its content set size
    size = int(len(contents)/len(source_nodes))
    i = 0
    for v in source_nodes:
        #the last source node will have slide more contents than others, to cover all the contents in the global set
        if (i == (len(source_nodes)-1)):
            for c in contents[(size*i+1):]:
                content_placement[random.choice(v)].add(c)
        else:
            for c in contents[(size*i+1):(size*(i+1)+1)]:
                content_placement[random.choice(v)].add(c)
        i+=1
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
