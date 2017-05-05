"""This module contains all configuration information used to run simulations
    """
from multiprocessing import cpu_count
from collections import deque
import copy
from icarus.util import Tree

# GENERAL SETTINGS

# Level of logging output
# Available options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = 'INFO'

# If True, executes simulations in parallel using multiple processes
# to take advantage of multicore CPUs
PARALLEL_EXECUTION = False

# Number of processes used to run simulations in parallel.
# This option is ignored if PARALLEL_EXECUTION = False
N_PROCESSES = cpu_count()/2

# Granularity of caching.
# Currently, only OBJECT is supported
CACHING_GRANULARITY = 'OBJECT'

# Format in which results are saved.
# Result readers and writers are located in module ./icarus/results/readwrite.py
# Currently only PICKLE is supported
RESULTS_FORMAT = 'PICKLE'

# Number of times each experiment is replicated
# This is necessary for extracting confidence interval of selected metrics
N_REPLICATIONS = 1

# List of metrics to be measured in the experiments
# The implementation of data collectors are located in ./icaurs/execution/collectors.py
DATA_COLLECTORS = ['CACHE_HIT_RATIO', 'LATENCY','LINK_LOAD' ]

# Range of alpha values of the Zipf distribution using to generate content requests
# alpha values must be positive. The greater the value the more skewed is the
# content popularity distribution
# Range of alpha values of the Zipf distribution using to generate content requests
# alpha values must be positive. The greater the value the more skewed is the
# content popularity distribution
# Note: to generate these alpha values, numpy.arange could also be used, but it
# is not recommended because generated numbers may be not those desired.
# E.g. arange may return 0.799999999999 instead of 0.8.
# This would give problems while trying to plot the results because if for
# example I wanted to filter experiment with alpha=0.8, experiments with
# alpha = 0.799999999999 would not be recognized
ALPHA = [1.0]

# Total size of network cache as a fraction of content population
NETWORK_CACHE = [ 0.7,  0.9]#, 0.15, 0.2, 0.25]#, 0.009, 0.01, 0.05, 0.1]

DIFF = [0.2]

# Number of content objects
N_CONTENTS = 1*10**5
# Number of requests per second (over the whole network)
NETWORK_REQUEST_RATE = 150.0

# Number of content requests generated to prepopulate the caches
# These requests are not logged
N_WARMUP_REQUESTS = 3*10**5

# Number of content requests generated after the warmup and logged
# to generate results.
N_MEASURED_REQUESTS = 10*10**5

# List of all implemented topologies
# Topology implementations are located in ./icarus/scenarios/topology.py
TOPOLOGIES =  [
                'MULTIAS'
#               'ROCKET_FUEL'
#               'GEANT'#,
#               'DATACENTER'
#               'GEANT'
#               'GARR',
#               'TISCALI'
               ]

ASNS = [
        1239,
        #1755,
        3257,
        #3967,
        6461
        ]


# List of caching and routing strategies
# The code is located in ./icarus/models/strategy.py
STRATEGIES = [
              'NRR',
              'EDGE',
              #'HR_SYMM',         # Symmetric hash-routing
              #'HR_ASYMM',        # Asymmetric hash-routing
              #'HR_MULTICAST',    # Multicast hash-routing
              #'HR_HYBRID_AM',    # Hybrid Asymm-Multicast hash-routing
              #'HR_HYBRID_SM',    # Hybrid Symm-Multicast hash-routing
              #'CL4M',            # Cache less for more
              'PROB_CACHE',      # ProbCache
              #'LCD',             # Leave Copy Down
              #'LCE',
              'BROKER_ASSISTED'
              #'RAND_CHOICE',     # Random choice: cache in one random cache on path
              #'RAND_BERNOULLI'  # Random Bernoulli: cache randomly in caches on path
              ]

WORKLOADS = [
#             'ALLSAME',
#	     'DIFFALPHA',
#	     'GROUPDIFFALPHA',	
             'DIFFRANK'#,
#             'GROUPDIFFRANK',
#             'ALLDIFF',
#             'GROUPALLDIFFRANK',
#             'GROUPALLDIFF'
            ]

# Cache replacement policy used by the network caches.
# Supported policies are: 'LRU', 'LFU', 'FIFO', 'RAND' and 'NULL'
# Cache policy implmentations are located in ./icarus/models/cache.py
CACHE_POLICY = 'LRU'

RANK_SUM = [3]
RANK_DIFF = [1]

# Queue of experiments
EXPERIMENT_QUEUE = deque()
default = Tree()

#default['topology']['name'] = 'ROCKET_FUEL'
#default['topology']['asn'] = 0000

#default['test_strategy'] = {
                            #'name': 'EDGE'
                            #}



default['workload'] = {
#                        'name':      'GROUP',
#                        'rank_diff': RANK_DIFF,
                        'n_contents': N_CONTENTS,
                        #'group_of_user': GROUP_OF_USER,
                        #'rank_diff': RANK_DIFF,
                        'n_warmup':   N_WARMUP_REQUESTS,
                        'n_measured': N_MEASURED_REQUESTS,
                        'rate':       NETWORK_REQUEST_RATE
                        }
default['cache_placement']['name'] = 'UNIFORM'
#decide the size of cache in each icr_candidate
default['content_placement']['name'] = 'UNIFORM'
#decide the content in each source
default['cache_policy']['name'] = CACHE_POLICY

# Create experiments multiplexing all desired parameters
for rank_sum in RANK_SUM:
    for alpha in ALPHA:
        for network_cache in NETWORK_CACHE:
            for topology in TOPOLOGIES:
                for strategy in STRATEGIES:
                    for diff in DIFF:
                        for workload in WORKLOADS:
                            for rank_diff in RANK_DIFF:
                                for network_cache in NETWORK_CACHE:
                                    experiment = copy.deepcopy(default)
                                    experiment['topology']['name'] = topology
                                    experiment['topology']['asns'] = ASNS
                                    experiment['workload']['name'] = workload
                                    experiment['workload']['rank_diff'] = rank_diff
                                    experiment['workload']['rank_sum'] = rank_sum
                                    experiment['workload']['network_cache'] = network_cache
                                    experiment['workload']['diff'] = diff
                                    experiment['workload']['alpha'] = alpha
                                    experiment['strategy']['name'] = strategy
                                    #experiment['strategy']['metacaching'] = 'LCE'
                                    #experiment['strategy']['sharedSet'] = SHAREDSET
                                    experiment['cache_placement']['network_cache'] = network_cache
                                    experiment['desc'] = "topology: %s, strategy: %s, diff: %s, Alpha: %s, rank_sum: %s, workload :%s, rank_diff: %s,  network cache: %s" \
                                                            % (topology, strategy, str(diff), str(alpha), str(rank_sum), workload, str(rank_diff), str(network_cache))
                                    EXPERIMENT_QUEUE.append(experiment)
