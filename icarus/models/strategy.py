"""Implementations of all caching and routing strategies
"""
from __future__ import division
import random
import abc
import collections

import networkx as nx

from icarus.registry import register_strategy
from icarus.util import inheritdoc, multicast_tree, path_links
from icarus.scenarios.algorithms import extract_cluster_level_topology


__all__ = [
       'Strategy',
       'Hashrouting',
       'HashroutingEdge',
       'HashroutingOnPath',
       'HashroutingClustered',
       'HashroutingSymmetric',
       'HashroutingAsymmetric',
       'HashroutingMulticast',
       'HashroutingHybridAM',
       'HashroutingHybridSM',
       'NoCache',
       'Partition',
       'Edge',
       'LeaveCopyEverywhere',
       'LeaveCopyDown',
       'CacheLessForMore',
       'RandomBernoulli',
       'RandomChoice',
       'NearestReplicaRouting',
           ]


class Strategy(object):
    """Base strategy imported by all other strategy classes"""

    __metaclass__ = abc.ABCMeta

    def __init__(self, view, controller, **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        kwargs : keyworded arguments, optional
            Additional strategy parameters
        """
        self.view = view
        self.controller = controller

    @abc.abstractmethod
    def process_event(self, time, receiver, content, log):
        """Process an event received from the simulation engine.

        This event is processed by executing relevant actions of the network
        controller, potentially based on the current status of the network
        retrieved from the network view.

        Parameters
        ----------
        time : int
            The timestamp of the event
        receiver : any hashable type
            The receiver node requesting a content
        content : any hashable type
            The content identifier requested by the receiver
        log : bool
            Indicates whether the event must be registered by the data
            collectors attached to the network.
        """
        raise NotImplementedError('The selected strategy must implement '
                                  'a process_event method')


class Hashrouting(Strategy):
    """Base class for all hash-routing implementations. Hash-routing
    implementations are described in [1]_.

    References
    ----------
    .. [1] L. Saino, I. Psaras and G. Pavlou, Hash-routing Schemes for
    Information-Centric Networking, in Proceedings of ACM SIGCOMM ICN'13
    workshop. Available:
    https://www.ee.ucl.ac.uk/~lsaino/publications/hashrouting-icn13.pdf
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(Hashrouting, self).__init__(view, controller)
        self.cache_nodes = view.cache_nodes()
        self.n_cache_nodes = len(self.cache_nodes)
        # Allocate results of hash function to caching nodes
        self.cache_assignment = {i: self.cache_nodes[i]
                                 for i in range(len(self.cache_nodes))}
        # Check if there are clusters
        if 'clusters' in self.view.topology().graph:
            self.clusters = self.view.topology().graph['clusters']
            # Convert to list in case it comes as set or iterable
            for i, cluster in enumerate(self.clusters):
                self.clusters[i] = list(cluster)
            self.cluster_size = {i: len(self.clusters[i])
                                 for i in range(len(self.clusters))}

    def authoritative_cache(self, content, cluster=None):
        """Return the authoritative cache node for the given content

        Parameters
        ----------
        content : any hashable type
            The identifier of the content
        cluster : int, optional
            If the topology is divided in clusters, then retun the authoritative
            cache responsible for the content in the specified cluster

        Returns
        -------
        authoritative_cache : any hashable type
            The node on which the authoritative cache is deployed
        """
        # TODO: I should probably consider using a better non-cryptographic hash
        # function, like xxhash
        h = hash(content)
        if cluster is not None:
            return self.clusters[cluster][h % self.cluster_size[cluster]]
        return self.cache_assignment[h % self.n_cache_nodes]


@register_strategy('HASHROUTING')
class BaseHashrouting(Hashrouting):
    """Unified implementation of the three basic hash-routing schemes:
    symmetric, asymmetric and multicast.
    """

    def __init__(self, view, controller, routing, **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        routing : str (SYMM | ASYMM | MULTICAST)
            Content routing option
        """
        super(BaseHashrouting, self).__init__(view, controller)
        self.routing = routing

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        # Forward request to authoritative cache
        self.controller.forward_request_path(receiver, cache)
        if self.controller.get_content(cache):
            # We have a cache hit here
            self.controller.forward_content_path(cache, receiver)
        else:
            # Cache miss: go all the way to source
            self.controller.forward_request_path(cache, source)
            if not self.controller.get_content(source):
                raise RuntimeError('The content is not found the expected source')
            if self.routing == 'SYMM':
                self.controller.forward_content_path(source, cache)
                # Insert in cache
                self.controller.put_content(cache)
                # Forward to receiver
                self.controller.forward_content_path(cache, receiver)
            elif self.routing == 'ASYMM':
                if cache in self.view.shortest_path(source, receiver):
                    # Forward to cache
                    self.controller.forward_content_path(source, cache)
                    # Insert in cache
                    self.controller.put_content(cache)
                    # Forward to receiver
                    self.controller.forward_content_path(cache, receiver)
                else:
                    # Forward to receiver straight away
                    self.controller.forward_content_path(source, receiver)
            elif self.routing == 'MULTICAST':
                if cache in self.view.shortest_path(source, receiver):
                    self.controller.forward_content_path(source, cache)
                    # Insert in cache
                    self.controller.put_content(cache)
                    # Forward to receiver
                    self.controller.forward_content_path(cache, receiver)
                else:
                    # Multicast
                    cache_path = self.view.shortest_path(source, cache)
                    recv_path = self.view.shortest_path(source, receiver)

                    # find what is the node that has to fork the content flow
                    for i in range(1, min([len(cache_path), len(recv_path)])):
                        if cache_path[i] != recv_path[i]:
                            fork_node = cache_path[i - 1]
                            break
                    else:
                        fork_node = cache
                    self.controller.forward_content_path(source, fork_node)
                    self.controller.forward_content_path(fork_node, receiver)
                    self.controller.forward_content_path(fork_node, cache,
                                                         main_path=False)
                self.controller.put_content(cache)
            else:
                raise ValueError("Routing %s not supported" % self.routing)
        self.controller.end_session()


@register_strategy('HR_EDGE_CACHE')
class HashroutingEdge(Hashrouting):
    """Hash-routing with a fraction of the cache operated un-coordinatedly at
    each PoP. Here we assume that each receiver is directly connected to one
    gateway, which is on the path to all other caches
    """

    def __init__(self, view, controller, routing, edge_cache_ratio, **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        routing : str
            Content routing scheme: SYMM, ASYMM or MULTICAST
        edge_cache_ratio : float [0, 1]
            Ratio of cache allocated to uncoordinated edge cache
        """
        if edge_cache_ratio < 0 or edge_cache_ratio > 1:
            raise ValueError('edge_cache_ratio must be between 0 and 1')
        super(HashroutingEdge, self).__init__(view, controller)
        self.routing = routing
        self.controller.reserve_local_cache(edge_cache_ratio)
        self.proxy = {v: list(self.view.topology().edge[v].keys())[0]
                        for v in self.view.topology().receivers()}
        if any(v not in self.view.topology().cache_nodes() for v in self.proxy.values()):
            raise ValueError('There are receivers connected to a proxy without cache')

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        proxy = self.proxy[receiver]
        self.controller.forward_request_hop(receiver, proxy)
        if proxy != cache:
            if self.controller.get_content_local_cache(proxy):
                self.controller.forward_content_hop(proxy, receiver)
                self.controller.end_session()
                return
            else:
                # Forward request to authoritative cache
                self.controller.forward_request_path(proxy, cache)
        if self.controller.get_content(cache):
            # We have a cache hit here
            self.controller.forward_content_path(cache, proxy)
        else:
            # Cache miss: go all the way to source
            self.controller.forward_request_path(cache, source)
            if not self.controller.get_content(source):
                raise RuntimeError('The content is not found the expected source')
            if self.routing == 'SYMM':
                self.controller.forward_content_path(source, cache)
                # Insert in cache
                self.controller.put_content(cache)
                # Forward to receiver
                self.controller.forward_content_path(cache, proxy)
            elif self.routing == 'ASYMM':
                if cache in self.view.shortest_path(source, proxy):
                    # Forward to cache
                    self.controller.forward_content_path(source, cache)
                    # Insert in cache
                    self.controller.put_content(cache)
                    # Forward to receiver
                    self.controller.forward_content_path(cache, proxy)
                else:
                    # Forward to receiver straight away
                    self.controller.forward_content_path(source, proxy)
            elif self.routing == 'MULTICAST':
                if cache in self.view.shortest_path(source, proxy):
                    self.controller.forward_content_path(source, cache)
                    # Insert in cache
                    self.controller.put_content(cache)
                    # Forward to receiver
                    self.controller.forward_content_path(cache, receiver)
                else:
                    # Multicast
                    cache_path = self.view.shortest_path(source, cache)
                    recv_path = self.view.shortest_path(source, proxy)

                    # find what is the node that has to fork the content flow
                    for i in range(1, min([len(cache_path), len(recv_path)])):
                        if cache_path[i] != recv_path[i]:
                            fork_node = cache_path[i - 1]
                            break
                    else: fork_node = cache
                    self.controller.forward_content_path(source, fork_node)
                    self.controller.forward_content_path(fork_node, proxy)
                    self.controller.forward_content_path(fork_node, cache, main_path=False)
                self.controller.put_content(cache)
            else:
                raise ValueError("Routing %s not recognized" % self.routing)

        if proxy != cache:
            self.controller.put_content_local_cache(proxy)
        self.controller.forward_content_hop(proxy, receiver)
        self.controller.end_session()


@register_strategy('HR_ON_PATH')
class HashroutingOnPath(Hashrouting):
    """Hash-routing with a fraction of the cache operated un-coordinatedly at
    each PoP

    This strategy differs from HashroutingEdge for the fact that in
    HashroutingEdge, the local fraction of the cache is queried only by traffic
    of endpoints directly attached to the caching node. In HashroutingOnPath
    the local cache is queried by all traffic being forwarded by the node.
    """

    def __init__(self, view, controller, routing, on_path_cache_ratio, **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        routing : str
            Content routing scheme: SYMM, ASYMM or MULTICAST
        on_path_cache_ratio : float [0, 1]
            Ratio of cache allocated to uncoordinated on-path cache
        """
        if on_path_cache_ratio < 0 or on_path_cache_ratio > 1:
            raise ValueError('on_path_cache_ratio must be between 0 and 1')
        super(HashroutingOnPath, self).__init__(view, controller)
        self.routing = routing
        self.controller.reserve_local_cache(on_path_cache_ratio)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        # Forward request to authoritative cache and check all local caches on path
        path = self.view.shortest_path(receiver, cache)
        for u, v in path_links(path):
            self.controller.forward_request_hop(u, v)
            if v != cache:
                if self.controller.get_content_local_cache(v):
                    serving_node = v
                    direct_return = True
                    break
        else:
            # No cache hits from local caches on path, query authoritative cache
            if self.controller.get_content(cache):
                serving_node = v
                direct_return = True
            else:
                path = self.view.shortest_path(cache, source)
                for u, v in path_links(path):
                    self.controller.forward_request_hop(u, v)
                    if v != source:
                        if self.controller.get_content_local_cache(v):
                            serving_node = v
                            direct_return = False
                            break
                else:
                    # No hits from local caches in cache -> source path
                    # Get content from the source
                    self.controller.get_content(source)
                    serving_node = source
                    direct_return = False
        # Now we have a serving node, let's return the content, while storing
        # it on all opportunistic caches on the path
        if direct_return:
            # Here I just need to return the content directly to the user
            path = list(reversed(self.view.shortest_path(receiver, serving_node)))
            for u, v in path_links(path):
                self.controller.forward_content_hop(u, v)
                if v != receiver:
                    self.controller.put_content_local_cache(v)
            self.controller.end_session()
            return
        # Here I need to see whether I need symm, asymm or multicast delivery
        if self.routing == 'SYMM':
            links = path_links(list(reversed(self.view.shortest_path(cache, serving_node)))) + \
                   path_links(list(reversed(self.view.shortest_path(receiver, cache))))
            for u, v in links:
                self.controller.forward_content_hop(u, v)
                if v == cache:
                    self.controller.put_content(v)
                else:
                    self.controller.put_content_local_cache(v)
        elif self.routing == 'ASYMM':
            path = list(reversed(self.view.shortest_path(receiver, serving_node)))
            for u, v in path_links(path):
                self.controller.forward_content_hop(u, v)
                if v == cache:
                    self.controller.put_content(v)
                else:
                    self.controller.put_content_local_cache(v)
        elif self.routing == 'MULTICAST':
            main_path = set(path_links(self.view.shortest_path(serving_node, receiver)))
            mcast_tree = multicast_tree(self.view.all_pairs_shortest_paths(), serving_node, [receiver, cache])
            cache_branch = mcast_tree.difference(main_path)
            for u, v in cache_branch:
                self.controller.forward_content_hop(u, v, main_path=False)
                if v == cache:
                    self.controller.put_content(v)
                else:
                    self.controller.put_content_local_cache(v)
            for u, v in main_path:
                self.controller.forward_content_hop(u, v, main_path=True)
                if v == cache:
                    self.controller.put_content(v)
                else:
                    self.controller.put_content_local_cache(v)
        else:
            raise ValueError("Routing %s not supported" % self.routing)
        self.controller.end_session()


@register_strategy('HR_CLUSTER')
class HashroutingClustered(Hashrouting):
    """Hash-routing all together in a single strategy"""

    def __init__(self, view, controller, intra_routing, inter_routing='LCE',
                 **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        intra_routing : str
            Intra-cluster content routing scheme: SYMM, ASYMM or MULTICAST
        inter_routing : str
            Inter-cluster content routing scheme. Only supported LCE
        """
        super(HashroutingClustered, self).__init__(view, controller)
        if intra_routing not in ('SYMM', 'ASYMM', 'MULTICAST'):
            raise ValueError('Intra-cluster routing policy %s not supported'
                             % intra_routing)
        self.intra_routing = intra_routing
        self.inter_routing = inter_routing
        self.cluster_topology = extract_cluster_level_topology(view.topology())
        self.cluster_sp = nx.all_pairs_shortest_path(self.cluster_topology)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)

        receiver_cluster = self.view.cluster(receiver)
        source_cluster = self.view.cluster(source)
        cluster_path = self.cluster_sp[receiver_cluster][source_cluster]

        if self.inter_routing == 'LCE':
            start = receiver
            for cluster in cluster_path:
                cache = self.authoritative_cache(content, cluster)
                # Forward request to authoritative cache
                self.controller.forward_request_path(start, cache)
                start = cache
                if self.controller.get_content(cache):
                    break
            else:
                # Loop was never broken, cache miss
                self.controller.forward_request_path(start, source)
                start = source
                if not self.controller.get_content(source):
                    raise RuntimeError('The content is not found the expected source')
        elif self.inter_routing == 'EDGE':
            cache = self.authoritative_cache(content, receiver_cluster)
            self.controller.forward_request_path(receiver, cache)
            if self.controller.get_content(cache):
                self.controller.forward_content_path(cache, receiver)
                self.controller.end_session()
                return
            else:
                self.controller.forward_request_path(cache, source)
                self.controller.get_content(source)
                cluster = source_cluster
                start = source

        # Now "start" is the node that is serving the content
        cluster_path = list(reversed(self.cluster_sp[receiver_cluster][cluster]))
        if self.inter_routing == 'LCE':
            if self.intra_routing == 'SYMM':
                for cluster in cluster_path:
                    cache = self.authoritative_cache(content, cluster)
                    # Forward request to authoritative cache
                    self.controller.forward_content_path(start, cache)
                    self.controller.put_content(cache)
                    start = cache
                self.controller.forward_content_path(start, receiver)
            elif self.intra_routing == 'ASYMM':
                self.controller.forward_content_path(start, receiver)
                path = self.view.shortest_path(start, receiver)
                traversed_clusters = set(self.view.cluster(v) for v in path)
                authoritative_caches = set(self.authoritative_cache(content, cluster)
                                        for cluster in traversed_clusters)
                traversed_caches = authoritative_caches.intersection(set(path))
                for v in traversed_caches:
                    self.controller.put_content(v)
            elif self.intra_routing == 'MULTICAST':
                destinations = [self.authoritative_cache(content, cluster)
                                for cluster in cluster_path]
                for v in destinations:
                    self.controller.put_content(v)
                main_path = set(path_links(self.view.shortest_path(start, receiver)))
                mcast_tree = multicast_tree(self.view.all_pairs_shortest_paths(), start, destinations)
                mcast_tree = mcast_tree.difference(main_path)
                for u, v in mcast_tree:
                    self.controller.forward_content_hop(u, v, main_path=False)
                for u, v in main_path:
                    self.controller.forward_content_hop(u, v, main_path=True)
            else:
                raise ValueError("Intra-cluster routing %s not supported" % self.intra_routing)
        elif self.inter_routing == 'EDGE':
            if self.intra_routing == 'SYMM':
                cache = self.authoritative_cache(content, cluster_path[-1])
                self.controller.forward_content_path(start, cache)
                self.controller.forward_content_path(cache, receiver)
                path = self.view.shortest_path(start, receiver)
                traversed_clusters = set(self.view.cluster(v) for v in path)
                authoritative_caches = set(self.authoritative_cache(content, cluster)
                                        for cluster in traversed_clusters)
                traversed_caches = authoritative_caches.intersection(set(path))
                for v in traversed_caches:
                    self.controller.put_content(v)
                if cache not in traversed_caches:
                    self.controller.put_content(cache)
            elif self.intra_routing == 'ASYMM':
                self.controller.forward_content_path(start, receiver)
                path = self.view.shortest_path(start, receiver)
                traversed_clusters = set(self.view.cluster(v) for v in path)
                authoritative_caches = set(self.authoritative_cache(content, cluster)
                                        for cluster in traversed_clusters)
                traversed_caches = authoritative_caches.intersection(set(path))
                for v in traversed_caches:
                    self.controller.put_content(v)
            elif self.intra_routing == 'MULTICAST':
                cache = self.authoritative_cache(content, cluster_path[-1])
                self.controller.put_content(cache)
                main_path = set(path_links(self.view.shortest_path(start, receiver)))
                mcast_tree = multicast_tree(self.view.all_pairs_shortest_paths(), start, [cache])
                mcast_tree = mcast_tree.difference(main_path)
                for u, v in mcast_tree:
                    self.controller.forward_content_hop(u, v, main_path=False)
                for u, v in main_path:
                    self.controller.forward_content_hop(u, v, main_path=True)
        else:
            raise ValueError("Inter-cluster routing %s not supported" % self.inter_routing)
        self.controller.end_session()


@register_strategy('HR_SYMM')
class HashroutingSymmetric(BaseHashrouting):
    """Hash-routing with symmetric routing (HR SYMM)

    According to this strategy, each content is routed following the same path
    of the request.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(HashroutingSymmetric, self).__init__(view, controller, 'SYMM', **kwargs)


@register_strategy('HR_ASYMM')
class HashroutingAsymmetric(BaseHashrouting):
    """Hash-routing with asymmetric routing (HR ASYMM)

    According to this strategy, each content fetched from an original source,
    as a result of a cache miss, is routed towards the receiver following the
    shortest path. If the authoritative cache is on the path, then it caches
    the content, otherwise not.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(HashroutingAsymmetric, self).__init__(view, controller, 'ASYMM', **kwargs)


@register_strategy('HR_MULTICAST')
class HashroutingMulticast(BaseHashrouting):
    """
    Hash-routing implementation with multicast delivery of content packets.

    In this strategy, if there is a cache miss, when contents return in
    the domain, they are multicast. One copy is sent to the authoritative cache
    and the other to the receiver. If the cache is on the path from source to
    receiver, this strategy behaves as a normal symmetric hash-routing
    strategy.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(HashroutingMulticast, self).__init__(view, controller, 'MULTICAST', **kwargs)


@register_strategy('HR_HYBRID_AM')
class HashroutingHybridAM(Hashrouting):
    """Hash-routing implementation with hybrid asymmetric-multicast delivery of
    content packets.

    In this strategy, if there is a cache miss, when content packets return in
    the domain, the packet is delivered to the receiver following the shortest
    path. If the additional number of hops required to send a copy to the
    authoritative cache is below a specific fraction of the network diameter,
    then one copy is sent to the authoritative cache as well. If the cache is
    on the path from source to receiver, this strategy behaves as a normal
    symmetric hash-routing strategy.
    """

    def __init__(self, view, controller, max_stretch=0.2, **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        max_stretch : float, optional
            The threshold path stretch (normalized by network diameter) set
            to decide whether using asymmetric or multicast routing. If the
            path stretch required to deliver a content is above max_stretch
            asymmetric delivery is used, otherwise multicast delivery is used.
        """
        super(HashroutingHybridAM, self).__init__(view, controller)
        self.max_stretch = nx.diameter(view.topology()) * max_stretch

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        # Forward request to authoritative cache
        self.controller.forward_request_path(receiver, cache)
        if self.controller.get_content(cache):
            # We have a cache hit here
            self.controller.forward_content_path(cache, receiver)
        else:
            # Cache miss: go all the way to source
            self.controller.forward_request_path(cache, source)
            if not self.controller.get_content(source):
                raise RuntimeError('The content was not found at the expected source')

            if cache in self.view.shortest_path(source, receiver):
                # Forward to cache
                self.controller.forward_content_path(source, cache)
                # Insert in cache
                self.controller.put_content(cache)
                # Forward to receiver
                self.controller.forward_content_path(cache, receiver)
            else:
                # Multicast
                cache_path = self.view.shortest_path(source, cache)
                recv_path = self.view.shortest_path(source, receiver)

                # find what is the node that has to fork the content flow
                for i in range(1, min([len(cache_path), len(recv_path)])):
                    if cache_path[i] != recv_path[i]:
                        fork_node = cache_path[i - 1]
                        break
                else: fork_node = cache
                self.controller.forward_content_path(source, receiver, main_path=True)
                # multicast to cache only if stretch is under threshold
                if len(self.view.shortest_path(fork_node, cache)) - 1 < self.max_stretch:
                    self.controller.forward_content_path(fork_node, cache, main_path=False)
                    self.controller.put_content(cache)
        self.controller.end_session()


@register_strategy('HR_HYBRID_SM')
class HashroutingHybridSM(Hashrouting):
    """
    Hash-routing implementation with hybrid symmetric-multicast delivery of
    content packets.

    In this implementation, the edge router receiving a content packet decides
    whether to deliver the packet using multicast or symmetric hash-routing
    based on the total cost for delivering the Data to both cache and receiver
    in terms of hops.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(HashroutingHybridSM, self).__init__(view, controller)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        cache = self.authoritative_cache(content)
        # handle (and log if required) actual request
        self.controller.start_session(time, receiver, content, log)
        # Forward request to authoritative cache
        self.controller.forward_request_path(receiver, cache)
        if self.controller.get_content(cache):
            # We have a cache hit here
            self.controller.forward_content_path(cache, receiver)
        else:
            # Cache miss: go all the way to source
            self.controller.forward_request_path(cache, source)
            if not self.controller.get_content(source):
                raise RuntimeError('The content is not found the expected source')

            if cache in self.view.shortest_path(source, receiver):
                self.controller.forward_content_path(source, cache)
                # Insert in cache
                self.controller.put_content(cache)
                # Forward to receiver
                self.controller.forward_content_path(cache, receiver)
            else:
                # Multicast
                cache_path = self.view.shortest_path(source, cache)
                recv_path = self.view.shortest_path(source, receiver)

                # find what is the node that has to fork the content flow
                for i in range(1, min([len(cache_path), len(recv_path)])):
                    if cache_path[i] != recv_path[i]:
                        fork_node = cache_path[i - 1]
                        break
                else: fork_node = cache

                symmetric_path_len = len(self.view.shortest_path(source, cache)) + \
                                     len(self.view.shortest_path(cache, receiver)) - 2
                multicast_path_len = len(self.view.shortest_path(source, fork_node)) + \
                                     len(self.view.shortest_path(fork_node, cache)) + \
                                     len(self.view.shortest_path(fork_node, receiver)) - 3

                self.controller.put_content(cache)
                # If symmetric and multicast have equal cost, choose symmetric
                # because of easier packet processing
                if symmetric_path_len <= multicast_path_len:  # use symmetric delivery
                    # Symmetric delivery
                    self.controller.forward_content_path(source, cache, main_path=True)
                    self.controller.forward_content_path(cache, receiver, main_path=True)
                else:
                    # Multicast delivery
                    self.controller.forward_content_path(source, receiver, main_path=True)
                    self.controller.forward_content_path(fork_node, cache, main_path=False)
                self.controller.end_session()


@register_strategy('NO_CACHE')
class NoCache(Strategy):
    """Strategy without any caching

    This corresponds to the traffic in a normal TCP/IP network without any
    CDNs or overlay caching, where all content requests are served by the
    original source.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(NoCache, self).__init__(view, controller)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source
        self.controller.start_session(time, receiver, content, log)
        self.controller.forward_request_path(receiver, source)
        self.controller.get_content(source)
        # Route content back to receiver
        path = list(reversed(path))
        self.controller.forward_content_path(source, receiver, path)
        self.controller.end_session()


@register_strategy('PARTITION')
class Partition(Strategy):
    """Partition caching strategy.

    In this strategy the network is divided into as many partitions as the number
    of caching nodes and each receiver is statically mapped to one and only one
    caching node. When a request is issued it is forwarded to the cache mapped
    to the receiver. In case of a miss the request is routed to the source and
    then returned to cache, which will store it and forward it back to the
    receiver.

    This requires median cache placement, which optimizes the placement of
    caches for this strategy.

    This strategy is normally used with a small number of caching nodes. This
    is the the behaviour normally adopted by Network CDN (NCDN). Google Global
    Cache (GGC) operates this way.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller):
        super(Partition, self).__init__(view, controller)
        if 'cache_assignment' not in self.view.topology().graph:
            raise ValueError('The topology does not have cache assignment '
                             'information. Have you used the optimal median '
                             'cache assignment?')
        self.cache_assignment = self.view.topology().graph['cache_assignment']

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        source = self.view.content_source(content)
        self.controller.start_session(time, receiver, content, log)
        cache = self.cache_assignment[receiver]
        self.controller.forward_request_path(receiver, cache)
        if not self.controller.get_content(cache):
            self.controller.forward_request_path(cache, source)
            self.controller.get_content(source)
            self.controller.forward_content_path(source, cache)
            self.controller.put_content(cache)
        self.controller.forward_content_path(cache, receiver)
        self.controller.end_session()


@register_strategy('EDGE')
class Edge(Strategy):
    """Edge caching strategy.

    In this strategy only a cache at the edge is looked up before forwarding
    a content request to the original source.

    In practice, this is like an LCE but it only queries the first cache it
    finds in the path. It is assumed to be used with a topology where each
    PoP has a cache but it simulates a case where the cache is actually further
    down the access network and it is not looked up for transit traffic passing
    through the PoP but only for PoP-originated requests.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller):
        super(Edge, self).__init__(view, controller)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source and queries caches on the path
        self.controller.start_session(time, receiver, content, log)
        edge_cache = None
        for u, v in path_links(path):
            self.controller.forward_request_hop(u, v)
            if self.view.has_cache(v):
                edge_cache = v
                if self.controller.get_content(v):
                    serving_node = v
                else:
                    # Cache miss, get content from source
                    self.controller.forward_request_path(v, source)
                    self.controller.get_content(source)
                    serving_node = source
                break
        else:
            # No caches on the path at all, get it from source
            self.controller.get_content(v)
            serving_node = v

        # Return content
        path = list(reversed(self.view.shortest_path(receiver, serving_node)))
        self.controller.forward_content_path(serving_node, receiver, path)
        if serving_node == source:
            self.controller.put_content(edge_cache)
        self.controller.end_session()


@register_strategy('LCE')
class LeaveCopyEverywhere(Strategy):
    """Leave Copy Everywhere (LCE) strategy.

    In this strategy a copy of a content is replicated at any cache on the
    path between serving node and receiver.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(LeaveCopyEverywhere, self).__init__(view, controller)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source and queries caches on the path
        self.controller.start_session(time, receiver, content, log)
        for u, v in path_links(path):
            self.controller.forward_request_hop(u, v)
            if self.view.has_cache(v):
                if self.controller.get_content(v):
                    serving_node = v
                    break
            # No cache hits, get content from source
            self.controller.get_content(v)
            serving_node = v
        # Return content
        path = list(reversed(self.view.shortest_path(receiver, serving_node)))
        for u, v in path_links(path):
            self.controller.forward_content_hop(u, v)
            if self.view.has_cache(v):
                # insert content
                self.controller.put_content(v)
        self.controller.end_session()


@register_strategy('LCD')
class LeaveCopyDown(Strategy):
    """Leave Copy Down (LCD) strategy.

    According to this strategy, one copy of a content is replicated only in
    the caching node you hop away from the serving node in the direction of
    the receiver. This strategy is described in [2]_.

    Rereferences
    ------------
    ..[2] N. Laoutaris, H. Che, i. Stavrakakis, The LCD interconnection of LRU
          caches and its analysis.
          Available: http://cs-people.bu.edu/nlaout/analysis_PEVA.pdf
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(LeaveCopyDown, self).__init__(view, controller)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source and queries caches on the path
        self.controller.start_session(time, receiver, content, log)
        for u, v in path_links(path):
            self.controller.forward_request_hop(u, v)
            if self.view.has_cache(v):
                if self.controller.get_content(v):
                    serving_node = v
                    break
        else:
            # No cache hits, get content from source
            self.controller.get_content(v)
            serving_node = v
        # Return content
        path = list(reversed(self.view.shortest_path(receiver, serving_node)))
        # Leave a copy of the content only in the cache one level down the hit
        # caching node
        copied = False
        for u, v in path_links(path):
            self.controller.forward_content_hop(u, v)
            if not copied and v != receiver and self.view.has_cache(v):
                self.controller.put_content(v)
                copied = True
        self.controller.end_session()


@register_strategy('PROB_CACHE')
class ProbCache(Strategy):
    """ProbCache strategy [4]_

    This strategy caches content objects probabilistically on a path with a
    probability depending on various factors, including distance from source
    and destination and caching space available on the path.

    This strategy was originally proposed in [3]_ and extended in [4]_. This
    class implements the extended version described in [4]_. In the extended
    version of ProbCache the :math`x/c` factor of the ProbCache equation is
    raised to the power of :math`c`.

    References
    ----------
    ..[3] I. Psaras, W. Chai, G. Pavlou, Probabilistic In-Network Caching for
          Information-Centric Networks, in Proc. of ACM SIGCOMM ICN '12
          Available: http://www.ee.ucl.ac.uk/~uceeips/prob-cache-icn-sigcomm12.pdf
    ..[4] I. Psaras, W. Chai, G. Pavlou, In-Network Cache Management and
          Resource Allocation for Information-Centric Networks, IEEE
          Transactions on Parallel and Distributed Systems, 22 May 2014
          Available: http://doi.ieeecomputersociety.org/10.1109/TPDS.2013.304
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, t_tw=10):
        super(ProbCache, self).__init__(view, controller)
        self.t_tw = t_tw
        self.cache_size = view.cache_nodes(size=True)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source and queries caches on the path
        self.controller.start_session(time, receiver, content, log)
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            self.controller.forward_request_hop(u, v)
            if self.view.has_cache(v):
                if self.controller.get_content(v):
                    serving_node = v
                    break
        else:
            # No cache hits, get content from source
            self.controller.get_content(v)
            serving_node = v
        # Return content
        path = list(reversed(self.view.shortest_path(receiver, serving_node)))
        c = len([v for v in path if self.view.has_cache(v)])
        x = 0.0
        for hop in range(1, len(path)):
            u = path[hop - 1]
            v = path[hop]
            N = sum([self.cache_size[n] for n in path[hop - 1:]
                     if n in self.cache_size])
            if v in self.cache_size:
                x += 1
            self.controller.forward_content_hop(u, v)
            if v != receiver and v in self.cache_size:
                # The (x/c) factor raised to the power of "c" according to the
                # extended version of ProbCache published in IEEE TPDS
                prob_cache = float(N) / (self.t_tw * self.cache_size[v]) * (x / c) ** c
                if random.random() < prob_cache:
                    self.controller.put_content(v)
        self.controller.end_session()


@register_strategy('CL4M')
class CacheLessForMore(Strategy):
    """Cache less for more strategy [5]_.

    References
    ----------
    ..[5] W. Chai, D. He, I. Psaras, G. Pavlou, Cache Less for More in
          Information-centric Networks, in IFIP NETWORKING '12
          Available: http://www.ee.ucl.ac.uk/~uceeips/centrality-networking12.pdf
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, use_ego_betw=False, **kwargs):
        super(CacheLessForMore, self).__init__(view, controller)
        topology = view.topology()
        if use_ego_betw:
            self.betw = dict((v, nx.betweenness_centrality(nx.ego_graph(topology, v))[v])
                             for v in topology.nodes_iter())
        else:
            self.betw = nx.betweenness_centrality(topology)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source and queries caches on the path
        self.controller.start_session(time, receiver, content, log)
        for u, v in path_links(path):
            self.controller.forward_request_hop(u, v)
            if self.view.has_cache(v):
                if self.controller.get_content(v):
                    serving_node = v
                    break
        # No cache hits, get content from source
        else:
            self.controller.get_content(v)
            serving_node = v
        # Return content
        path = list(reversed(self.view.shortest_path(receiver, serving_node)))
        # get the cache with maximum betweenness centrality
        # if there are more than one cache with max betw then pick the one
        # closer to the receiver
        max_betw = -1
        designated_cache = None
        for v in path[1:]:
            if self.view.has_cache(v):
                if self.betw[v] >= max_betw:
                    max_betw = self.betw[v]
                    designated_cache = v
        # Forward content
        for u, v in path_links(path):
            self.controller.forward_content_hop(u, v)
            if v == designated_cache:
                self.controller.put_content(v)
        self.controller.end_session()


@register_strategy('NRR')
class NearestReplicaRouting(Strategy):
    """Ideal Nearest Replica Routing (NRR) strategy.

    In this strategy, a request is forwarded to the topologically close node
    holding a copy of the requested item. This strategy is ideal, as it is
    implemented assuming that each node knows the nearest replica of a content
    without any signalling

    On the return path, content can be caching according to a variety of
    metacaching policies. LCE and LCD are currently supported.
    """

    def __init__(self, view, controller, metacaching, implementation='ideal',
                 radius=4, **kwargs):
        """Constructor

        Parameters
        ----------
        view : NetworkView
            An instance of the network view
        controller : NetworkController
            An instance of the network controller
        metacaching : str (LCE | LCD)
            Metacaching policy used
        implementation : str, optional
            The implementation of the nearest replica discovery. Currently on
            ideal routing is implemented, in which each node has omniscient
            knowledge of the location of each content.
        radius : int, optional
            Radius used by nodes to discover the location of a content. Not
            used by ideal routing.
        """
        super(NearestReplicaRouting, self).__init__(view, controller)
        if metacaching not in ('LCE', 'LCD'):
            raise ValueError("Metacaching policy %s not supported" % metacaching)
        if implementation not in ('ideal', 'approx_1', 'approx_2'):
            raise ValueError("Implementation %s not supported" % implementation)
        self.metacaching = metacaching
        self.implementation = implementation
        self.radius = radius
        self.distance = nx.all_pairs_dijkstra_path_length(self.view.topology(),
                                                          weight='delay')

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        locations = self.view.content_locations(content)
        nearest_replica = min(locations, key=lambda x: self.distance[receiver][x])
        # Route request to nearest replica
        self.controller.start_session(time, receiver, content, log)
        if self.implementation == 'ideal':
            self.controller.forward_request_path(receiver, nearest_replica)
        elif self.implementation == 'approx_1':
            # Floods actual request packets
            paths = {loc: len(self.view.shortest_path(receiver, loc)[:self.radius])
                     for loc in locations}
            # TODO: Continue
            raise NotImplementedError("Not implemented")
        elif self.implementation == 'approx_2':
            # Floods meta-request packets
            # TODO: Continue
            raise NotImplementedError("Not implemented")
        else:
            # Should never reach this block anyway
            raise ValueError("Implementation %s not supported"
                             % str(self.implementation))
        self.controller.get_content(nearest_replica)
        # Now we need to return packet and we have options
        path = list(reversed(self.view.shortest_path(receiver, nearest_replica)))
        if self.metacaching == 'LCE':
            for u, v in path_links(path):
                self.controller.forward_content_hop(u, v)
                if self.view.has_cache(v) and not self.view.cache_lookup(v, content):
                    self.controller.put_content(v)
        elif self.metacaching == 'LCD':
            copied = False
            for u, v in path_links(path):
                self.controller.forward_content_hop(u, v)
                if not copied and v != receiver and self.view.has_cache(v):
                    self.controller.put_content(v)
                    copied = True
        else:
            raise ValueError('Metacaching policy %s not supported'
                             % self.metacaching)
        self.controller.end_session()


@register_strategy('RAND_BERNOULLI')
class RandomBernoulli(Strategy):
    """Bernoulli random cache insertion.

    In this strategy, a content is randomly inserted in a cache on the path
    from serving node to receiver with probability *p*.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, p=0.2, **kwargs):
        super(RandomBernoulli, self).__init__(view, controller)
        self.p = p

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source and queries caches on the path
        self.controller.start_session(time, receiver, content, log)
        for u, v in path_links(path):
            self.controller.forward_request_hop(u, v)
            if self.view.has_cache(v):
                if self.controller.get_content(v):
                    serving_node = v
                    break
        else:
            # No cache hits, get content from source
            self.controller.get_content(v)
            serving_node = v
        # Return content
        path = list(reversed(self.view.shortest_path(receiver, serving_node)))
        for u, v in path_links(path):
            self.controller.forward_content_hop(u, v)
            if v != receiver and self.view.has_cache(v):
                if random.random() < self.p:
                    self.controller.put_content(v)
        self.controller.end_session()

@register_strategy('RAND_CHOICE')
class RandomChoice(Strategy):
    """Random choice strategy

    This strategy stores the served content exactly in one single cache on the
    path from serving node to receiver selected randomly.
    """

    @inheritdoc(Strategy)
    def __init__(self, view, controller, **kwargs):
        super(RandomChoice, self).__init__(view, controller)

    @inheritdoc(Strategy)
    def process_event(self, time, receiver, content, log):
        # get all required data
        source = self.view.content_source(content)
        path = self.view.shortest_path(receiver, source)
        # Route requests to original source and queries caches on the path
        self.controller.start_session(time, receiver, content, log)
        for u, v in path_links(path):
            self.controller.forward_request_hop(u, v)
            if self.view.has_cache(v):
                if self.controller.get_content(v):
                    serving_node = v
                    break
        else:
            # No cache hits, get content from source
            self.controller.get_content(v)
            serving_node = v
        # Return content
        path = list(reversed(self.view.shortest_path(receiver, serving_node)))
        caches = [v for v in path[1:-1] if self.view.has_cache(v)]
        designated_cache = random.choice(caches) if len(caches) > 0 else None
        for u, v in path_links(path):
            self.controller.forward_content_hop(u, v)
            if v == designated_cache:
                self.controller.put_content(v)
        self.controller.end_session()
