"""Functions for creating or importing topologies for experiments.

To create a custom topology, create a function returning an instance of the
`IcnTopology` class. An IcnTopology is simply a subclass of a Topology class
provided by FNSS.

A valid ICN topology must have the following attributes:
 * Each node must have one stack among: source, receiver, router
 * The topology must have an attribute called `icr_candidates` which is a set
   of router nodes on which a cache may be possibly deployed. Caches are not
   deployed directly at topology creation, instead they are deployed by a
   cache placement algorithm.
"""
from __future__ import division

from os import path
from random import random
from bisect import bisect
import networkx as nx
import fnss
import math
from icarus.registry import register_topology_factory


__all__ = [
        'IcnTopology',
        'topology_rocketfuel_latency'
           ]



# Delays
# These values are suggested by this Computer Networks 2011 paper:
# http://www.cs.ucla.edu/classes/winter09/cs217/2011CN_NameRouting.pdf
# which is citing as source of this data, measurements from this IMC'06 paper:
# http://www.mpi-sws.org/~druschel/publications/ds2-imc.pdf
INTERNAL_LINK_DELAY = 2
EXTERNAL_LINK_DELAY = 34

# Path where all topologies are stored
TOPOLOGY_RESOURCES_DIR = path.abspath(path.join(path.dirname(__file__),
                                                path.pardir, path.pardir,
                                                'resources', 'topologies'))


class IcnTopology(fnss.Topology):
    """Class modelling an ICN topology

    An ICN topology is a simple FNSS Topology with addition methods that
    return sets of caching nodes, sources and receivers.
    """

    def cache_nodes(self):
        """Return a dictionary mapping nodes with a cache and respective cache
        size

        Returns
        -------
        cache_nodes : dict
            Dictionary mapping node identifiers and cache size
        """
        return {v: self.node[v]['stack'][1]['cache_size']
                for v in self
                if 'stack' in self.node[v]
                and 'cache_size' in self.node[v]['stack'][1]
                }

    def sources(self):
        """Return a set of source nodes

        Returns
        -------
        sources : set
            Set of source nodes
        """
        return set(v for v in self
                   if 'stack' in self.node[v]
                   and self.node[v]['stack'][0] == 'source')

    def receivers(self):
        """Return a set of receiver nodes

        Returns
        -------
        receivers : set
            Set of receiver nodes
        """
        return set(v for v in self
                   if 'stack' in self.node[v]
                   and self.node[v]['stack'][0] == 'receiver')


@register_topology_factory('ROCKET_FUEL')
def topology_rocketfuel_latency(asn, source_ratio=0.1, ext_delay=EXTERNAL_LINK_DELAY, **kwargs):
    """Parse a generic RocketFuel topology with annotated latencies
    To each node of the parsed topology it is attached an artificial receiver
    node. To the routers with highest degree it is also attached a source node.
    Parameters
    ----------
    asn : int
        AS number
    source_ratio : float
        Ratio between number of source nodes (artificially attached) and routers
    ext_delay : float
        Delay on external nodes
    """
    if source_ratio < 0 or source_ratio > 1:
        raise ValueError('source_ratio must be comprised between 0 and 1')
    f_topo = path.join(TOPOLOGY_RESOURCES_DIR, 'rocketfuel-latency', str(asn), 'latencies.intra')
    topology = fnss.parse_rocketfuel_isp_latency(f_topo).to_undirected()
    topology = list(nx.connected_component_subgraphs(topology))[0]
    # First mark all current links as inernal
    for u, v in topology.edges_iter():
        topology.edge[u][v]['type'] = 'internal'
    # Note: I don't need to filter out nodes with degree 1 cause they all have
    # a greater degree value but we compute degree to decide where to attach sources
    routers = topology.nodes()

    # Source attachment
    n_sources = int(source_ratio * len(routers))
    sources = ['src_%d' % i for i in range(n_sources)]
    deg = nx.degree(topology)

    # Attach sources based on their degree purely, but they may end up quite clustered
    routers = sorted(routers, key=lambda k: deg[k], reverse=True)
    for i in range(len(sources)):
        topology.add_edge(sources[i], routers[i], delay=ext_delay, type='external')

    # Here let's try attach them via cluster
#     clusters = compute_clusters(topology, n_sources, distance=None, n_iter=1000)
#     source_attachments = [max(cluster, key=lambda k: deg[k]) for cluster in clusters]
#     for i in range(len(sources)):
#         topology.add_edge(sources[i], source_attachments[i], delay=ext_delay, type='external')

    # attach artificial receiver nodes to ICR candidates
    receivers = ['rec_%d' % i for i in range(len(routers))]
    for i in range(len(routers)):
        topology.add_edge(receivers[i], routers[i], delay=0, type='internal')
    # Set weights to latency values
    for u, v in topology.edges_iter():
        topology.edge[u][v]['weight'] = topology.edge[u][v]['delay']
    # Deploy stacks on nodes
    topology.graph['icr_candidates'] = set(routers)
    for v in sources:
        fnss.add_stack(topology, v, 'source')
    print (asn)
    print (sources)
    print (len(sources))
    for v in receivers:
        fnss.add_stack(topology, v, 'receiver')
    for v in routers:
        fnss.add_stack(topology, v, 'router')
    print (len(receivers))
    print (len(routers))
    return IcnTopology(topology)
