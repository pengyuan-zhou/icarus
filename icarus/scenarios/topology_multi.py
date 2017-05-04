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
        'topology_multi_as'
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


@register_topology_factory('MULTIAS')
def topology_multi_as(asns, source_ratio=0.1, ext_delay=EXTERNAL_LINK_DELAY, **kwargs):
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
    f_t = [ path.join(TOPOLOGY_RESOURCES_DIR, 'rocketfuel-latency', str(i), 'latencies.intra') for i in asns]
    topologytmp = [fnss.parse_rocketfuel_isp_latency(i).to_undirected() for i in f_t]
    topologylist = [list(nx.connected_component_subgraphs(i))[0] for i in topologytmp]
    # First mark all current links as inernal
    for topology in topologylist:
        j = topologylist.index(topology)
        while j>=0:
            topology=nx.relabel_nodes(topology,mapping, copy=False)
            j -= 1
    for topology in topologylist:
        for u, v in topology.edges_iter():
            topology.edge[u][v]['type'] = 'internal'
	
	# Note: I don't need to filter out nodes with degree 1 cause they all have
    # a greater degree value but we compute degree to decide where to attach sources
    
    routerslist = [topology.nodes() for topology in topologylist]
    # Source attachment
    n_sourceslist = [int(source_ratio * len(routers)) for routers in routerslist]
    sourceslist = [None] * len(n_sourceslist) 
    for n_sources in n_sourceslist:
        j = n_sourceslist.index(n_sources)
        sourceslist[j] =['src_%d_%d' % (j,i) for i in range(n_sources)]    
    
    deg = [nx.degree(topology) for topology in topologylist]

    # Attach sources based on their degree purely, but they may end up quite clustered
    routerslistsort = [ sorted(routers, key=lambda k: deg[routerslist.index(routers)][k], reverse=True) for routers in routerslist ]
    for sources in sourceslist:
        j = sourceslist.index(sources)
        for i in range(len(sources)):
            #intra AS link set as internal, source to router delay bigger than router to receiver
            topologylist[j].add_edge(sources[i], routerslistsort[j][i], delay=1, type='internal')
            #inter AS link set as external, AS_i source connect to AS_i+1(cycle of list)  router
            if j==(len(sourceslist)-1):
                topologylist[j].add_edge(sources[i], routerslistsort[0][i], delay=ext_delay, type='external')
            else:            
                topologylist[j].add_edge(sources[i], routerslistsort[j+1][i], delay=ext_delay, type='external')
  

    # attach artificial receiver nodes to ICR candidates
    receiverslist = [None]*len(routerslistsort)
    for routers in routerslistsort:
        j = routerslistsort.index(routers)
        receiverslist[j] = ['rec_%d_%d' % (j,i) for i in range(len(routers))]
        for i in range(len(routers)):
            topologylist[j].add_edge(receiverslist[j][i], routers[i], delay=0, type='internal')
    # Set weights to latency values
    for topology in topologylist:
        for u, v in topology.edges_iter():
            topology.edge[u][v]['weight'] = topology.edge[u][v]['delay']

    #multiple AS topology
    #we combine and import all the node,edge and attributes after individual definition of each AS
    #to provide scalability that being easier to change any one of them
    topo_multiAS = nx.Graph()
    for topology in topologylist:
        j = topologylist.index(topology)    
        for v in topology.nodes():
            topo_multiAS.add_node(v)
        topo_multiAS.add_edges_from(topology.edges())
        delays = nx.get_edge_attributes(topology, 'delay')
        types = nx.get_edge_attributes(topology, 'type')
        weights = nx.get_edge_attributes(topology, 'weight')
        nx.set_edge_attributes(topo_multiAS,'delay',delays)
        nx.set_edge_attributes(topo_multiAS,'type',types)
        nx.set_edge_attributes(topo_multiAS,'weight',weights)
        
        # Deploy stacks on nodes
        topo_multiAS.graph['icr_candidates'] = set(routerslistsort[j])
        for v in sourceslist[j]:
            fnss.add_stack(topo_multiAS, v, 'source')
        for v in receiverslist[j]:
            fnss.add_stack(topo_multiAS, v, 'receiver')
        for v in routerslistsort[j]:
            fnss.add_stack(topo_multiAS, v, 'router')
        
    return IcnTopology(topo_multiAS)

def mapping(x):
    return x+1000
