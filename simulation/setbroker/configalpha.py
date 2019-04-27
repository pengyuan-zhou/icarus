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
PARALLEL_EXECUTION = True

# Number of processes used to run simulations in parallel.
# This option is ignored if PARALLEL_EXECUTION = False
N_PROCESSES = cpu_count()

# Granularity of caching.
# Currently, only OBJECT is supported
CACHING_GRANULARITY = 'OBJECT'

# Format in which results are saved.
# Result readers and writers are located in module ./icarus/results/readwrite.py
# Currently only PICKLE is supported 
RESULTS_FORMAT = 'PICKLE'

# Number of times each experiment is replicated
# This is necessary for extracting confidence interval of selected metrics
N_REPLICATIONS = 20

# List of metrics to be measured in the experiments
# The implementation of data collectors are located in ./icaurs/execution/collectors.py
DATA_COLLECTORS = ['CACHE_HIT_RATIO', 'LATENCY', 'LINK_LOAD', 'PATH_STRETCH']

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
ALPHA = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
#ALPHA = [1.0]
# Total size of network cache as a fraction of content population
#NETWORK_CACHE = [0.001, 0.005, 0.01,0.015,0.02,0.025,0.03,0.035,0.04]#, 0.005, 0.01,0.015,0.02,0.025,0.03,0.035,0.04]
NETWORK_CACHE = [0.01]
# Number of content objects
N_CONTENTS = 1*10**4

# Number of requests per second (over the whole network)
NETWORK_REQUEST_RATE = 250.0

# Number of content requests generated to prepopulate the caches
# These requests are not logged
N_WARMUP_REQUESTS = 3*10**4

# Number of content requests generated after the warmup and logged
# to generate results. 
N_MEASURED_REQUESTS = 6*10**5

i=0
SHAREDSET= [None]*1
while i<1:
    SHAREDSET[i]= range(1,1+1000*(i+1))
    SHAREDSET[i].extend(range(10001,10001+1000*(i+1)))
    SHAREDSET[i].extend(range(20001,20001+1000*(i+1)))
    print (len(SHAREDSET[i]))
    i+=1

# List of all implemented topologies
# Topology implementations are located in ./icarus/scenarios/topology.py
TOPOLOGIES =  [
#        'GEANT',
#        'WIDE',
#        'GARR',
#        'TISCALI',
         'MULTIAS'
              ]

ASNS = [1221,1755,3967]

# List of caching and routing strategies
# The code is located in ./icarus/models/strategy.py
STRATEGIES = [
     #'LCE',             # Leave Copy Everywhere
     #'NO_CACHE',        # No caching, shorest-path routing
     #'HR_SYMM',         # Symmetric hash-routing
     #'HR_ASYMM',        # Asymmetric hash-routing
     #'HR_MULTICAST',    # Multicast hash-routing
     #'HR_HYBRID_AM',    # Hybrid Asymm-Multicast hash-routing
     #'HR_HYBRID_SM',    # Hybrid Symm-Multicast hash-routing
     #'BROKER_HR_HYBRID_SM',    # Hybrid Symm-Multicast hash-routing
     'CL4M',            # Cache less for more
     'BROKER_CL4M',            # Cache less for more
     'PROB_CACHE',      # ProbCache
     'BROKER_PROB_CACHE',      # ProbCache
     #'LCD',             # Leave Copy Down
     #'BROKER_LCD',             # Leave Copy Down
     #'NRR',     # Random choice: cache in one random cache on path
     #'RAND_BERNOULLI',  # Random Bernoulli: cache randomly in caches on path
     #'BROKER_ASSISTED_IDEAL'
             ]

# Cache replacement policy used by the network caches.
# Supported policies are: 'LRU', 'LFU', 'FIFO', 'RAND' and 'NULL'
# Cache policy implmentations are located in ./icarus/models/cache.py
CACHE_POLICY = 'LRU'
DIFF=0
RANK_SUM =3
RANK_DIFF = 1
# Queue of experiments
EXPERIMENT_QUEUE = deque()
default = Tree()
default['workload'] = {'name':       'DIFFRANK',
                       'n_contents': N_CONTENTS,
                       'rank_diff': RANK_DIFF,
                       'rank_sum': RANK_SUM,
                       'diff':       DIFF,
                       'n_warmup':   N_WARMUP_REQUESTS,
                       'n_measured': N_MEASURED_REQUESTS,
                       'rate':       NETWORK_REQUEST_RATE
                       }
default['cache_placement']['name'] = 'UNIFORM'
default['content_placement']['name'] = 'ASES'#'UNIFORM'
default['cache_policy']['name'] = CACHE_POLICY
default['topology']['asns'] = ASNS
# Create experiments multiplexing all desired parameters
for alpha in ALPHA:
    for strategy in STRATEGIES:
        for topology in TOPOLOGIES:
            for network_cache in NETWORK_CACHE:
                experiment = copy.deepcopy(default)
                experiment['workload']['alpha'] = alpha
                experiment['strategy']['name'] = strategy
                experiment['topology']['name'] = topology
                experiment['cache_placement']['network_cache'] = network_cache
                experiment['desc'] = "Alpha: %s, strategy: %s, topology: %s, network cache: %s" \
                                     % (str(alpha), strategy, topology, str(network_cache))
                EXPERIMENT_QUEUE.append(experiment)
