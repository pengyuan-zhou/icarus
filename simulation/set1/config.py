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
N_REPLICATIONS = 5

# List of metrics to be measured in the experiments
# The implementation of data collectors are located in ./icaurs/execution/collectors.py
DATA_COLLECTORS = ['CACHE_HIT_RATIO', 'LATENCY']

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
#80 percent contents can be cached intra group
NETWORK_CACHE = [0.1]

# Number of content objects
N_CONTENTS = 3*10**4

# Number of requests per second (over the whole network)
NETWORK_REQUEST_RATE = 300.0

# Number of content requests generated to prepopulate the caches
# These requests are not logged
N_WARMUP_REQUESTS = 6*10**4

# Number of content requests generated after the warmup and logged
# to generate results. 
N_MEASURED_REQUESTS = 6*10**5

# Number of workload ranks over all nodes 
N_RANK = 32

#generate topology
#nodes of group leader are generated by needed, not included in N_NODE
#N_CORE,N_NODE=map(int,raw_input("generating 3 layer datacenter network,\n \
        #input number of central data store, caching nodes seperated by commas:\n").split(','))
#N_SIZE=raw_input(" input list of group size, seperated by commas\n \
        #make sure number of nodes can be devided by group size:\n").split(',')
#N_SIZES= [int(x.strip()) for x in N_SIZE]

N_CORE = 1
N_NODE = 320
#group_num = N_NODE/N_SIZES :32,16,8,4,2,1
N_SIZES = [10, 20, 40, 80, 160, 320]

TOPOLOGIES = [
                'DATACENTER'
                ]
# List of caching and routing strategies
# The code is located in ./icarus/models/strategy/offpath.py
STRATEGIES = [
                'NRR' #Ideal Nearest Replica Routing (NRR) strategy     
            ]

# Cache replacement policy used by the network caches.
# Supported policies are: 'LRU', 'LFU', 'FIFO', 'RAND' and 'NULL'
# Cache policy implmentations are located in ./icarus/models/cache.py
CACHE_POLICY = 'LRU'

# Queue of experiments
EXPERIMENT_QUEUE = deque()
default = Tree()
default['workload'] = {'name':       'DIFFRANK',
                       'n_rank':     N_RANK,
                       'n_contents': N_CONTENTS,
                       'n_warmup':   N_WARMUP_REQUESTS,
                       'n_measured': N_MEASURED_REQUESTS,
                       'rate':       NETWORK_REQUEST_RATE
                       }
default['topology'] = { 
                        'n_datastore':N_CORE  
                        }
default['cache_placement']['name'] = 'UNIFORM'
default['content_placement']['name'] = 'UNIFORM'
default['cache_policy']['name'] = CACHE_POLICY
# Create experiments multiplexing all desired parameters
for alpha in ALPHA:
    for strategy in STRATEGIES:
        for topology in TOPOLOGIES:
            for network_cache in NETWORK_CACHE:
                for n_size in N_SIZES:
                    experiment = copy.deepcopy(default)
                    experiment['workload']['alpha'] = alpha
                    #overall number of workloads remain same, workloads intra group changes according to size
                    experiment['workload']['rank_per_group'] = int(N_RANK/(N_NODE/n_size))
                    experiment['strategy']['name'] = strategy
                    experiment['topology']['name'] = topology
                    experiment['topology']['n_node'] = N_NODE
                    experiment['topology']['n_member'] = n_size
                    experiment['cache_placement']['network_cache'] = network_cache
                    experiment['desc'] = "Alpha: %s, strategy: %s,  network cache: %s, topology: Datacenter,  num of datastore: %s, group size: %s. " % (str(alpha), strategy, str(network_cache), str(N_CORE), str(n_size) )
                    EXPERIMENT_QUEUE.append(experiment)
