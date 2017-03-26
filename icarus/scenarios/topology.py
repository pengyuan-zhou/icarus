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

import networkx as nx
import fnss

from icarus.registry import register_topology_factory


__all__ = [
        'IcnTopology',
        'topology_datacenter'
           ]


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


@register_topology_factory('DATACENTER')
def topology_datacenter(n_datastore, n_node, n_member,in_delay=2, out_delay=34, **kwargs):
    """Returns a 3 layer topology, with a source at core, n_members of
    receivers(with cache capacity) per leader.

    Parameters
    ----------
    n_datastore : int
        The number of central data store
    n_node : int
        The number of caching nodes
    n_member : int
        The number of members per group
    in_delay : float
        The link delay within group in milliseconds,by default 2
    out_delay: float
        The link delay between leaders and datastore in milliseconds, by default 34
        delay follows the original setting which 
        are suggested by this Computer Networks 2011 paper:
        http://www.cs.ucla.edu/classes/winter09/cs217/2011CN_NameRouting.pdf
        which is citing as source of this data, measurements from this IMC'06 paper:
        http://www.mpi-sws.org/~druschel/publications/ds2-imc.pdf
    Returns
    -------
    topology : IcnTopology
        The topology object
    """
    n_leader = int(n_node/n_member)
    
    topology = fnss.two_tier_topology(n_datastore, n_leader, n_member)
   
    #----------------nodes--------------#
    datastores = [v for v in topology.nodes_iter()
            if topology.node[v]['tier'] == 'core']
    
    #leaders don't cache
    leaders = [v for v in topology.nodes_iter()
            if topology.node[v]['tier'] == 'edge']
    
    #members have caching capacity
    members = [v for v in topology.nodes_iter() 
            if topology.node[v]['tier'] == 'leaf']
    
    for v in datastores:
        fnss.add_stack(topology, v, 'source')
    for v in leaders:
        fnss.add_stack(topology, v, 'router')
    for v in members:
        fnss.add_stack(topology, v, 'receiver')
    
    #-----------------cacheNodes--------------#
    topology.graph['icr_candidates'] = set(members)
    
    #Pre assign grouping result
    #members connecting to same leader belong to same group
    i = 1
    while i <= n_leader:
        for v in members[int(n_member*(i-1)):int(n_member*i)]:
            topology.node[v]['group'] = int(i)
            #print (i,v, topology.node[v]['group'])
        i += 1
    
    # assign weight 1 to all links
    fnss.set_weights_constant(topology, 1.0)
        
    # assign delay
    fnss.set_delays_constant(topology, in_delay, 'ms')
    
    # label links as internal or external

    #without grouping, exchange internal and external setting
    #this balance the path delay from member to datastore, while 
    #forcing member request to datastore instead of other members
    #leader in this case is just a conceptual layer instead of actual node
    if n_leader == 1 :
        for u, v in topology.edges():
            if u in members or v in members:
                topology.edge[u][v]['type'] = 'external'
                fnss.set_weights_constant(topology, 1000.0, [(u, v)])
                fnss.set_delays_constant(topology, out_delay, 'ms', [(u, v)])
            else:
                topology.edge[u][v]['type'] = 'internal'
    
    else :
        for u, v in topology.edges():
            if u in datastores or v in datastores:
                topology.edge[u][v]['type'] = 'external'
                # this prevents sources to be used to route traffic
                fnss.set_weights_constant(topology, 1000.0, [(u, v)])
                fnss.set_delays_constant(topology, out_delay, 'ms', [(u, v)])
                #print (u , v , topology.edge[u][v])
            else:
                topology.edge[u][v]['type'] = 'internal'
    return IcnTopology(topology)  
    
