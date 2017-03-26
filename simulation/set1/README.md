For Mecomm simulation.


## Run
To run the expriments and plot the results, execute the `run.sh` script:

    $ sh run.sh

## How does it work
The `config.py` contains all the configuration for executing experiments and
do plots. The `run.sh` script launches the Icarus simulator passing the configuration
file as an argument. The `plotresults.py` file provides functions for plotting
specific results based on `icarus.results.plot` functions.


##simulation process
important args:

N_CORE:  number of datastore (set to 1)
N_NODE: number of overall caching nodes 
N_SIZES: list of group size
N_RANK: number of overall workloads rank(one rank indicates one workload)
simulation:
for each group size, the nodes are equally divided to groups of the size. 
The workloads are also equally distributed to groups.
Generating one group leader for each group.
member-leader link normally has smaller delay than leader-datastore link.
When group size increases, higher proportion of member-leader links have larger delay than leader-datastore link.
Because larger group size means more distributed nodes. And then more nodes are fetching data directly from datastore. 

When "group size" equals to number of nodes, there is only one group, meaning there are no groups.
All workloads are distributed to nodes randomly. All nodes fetch data from data store.


Member can only get to datastore via leader.
Leader can only get to another leader via datastore.

 


##requirement to simplify config
Number of topo nodes needs to be able to be divided by "group size", to assure number of 
group is integer. 


Likewise, for each situation with different number of groups, number of workloads should be able to be 
divided by number of groups. So that workloads can be distributed consistently and equally to groups.
PS. To simulate with same backgroud, a set of simulations should have same number of workloads.
