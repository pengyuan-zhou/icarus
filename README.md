The code simulates resource cache grouping in an Edge-Fog cloud. The clustering strategy considers resources with similar interest types and maps them as part of the same group.

The major objectives that we are looking into are:

1) Reduction in latency (cache hits + network delay) by sharing data within the group i.e. retrieving data from cache of a group member vs. when there are no0 groups i.e. retrieving data from a central data store 

2) Effects of group size. That is changes to latency, data sharing when a) more number of smaller groups; and b) less number of bigger groups


1) and 2) are shown in same figures under ./simulation/set1/plots.$time/    ("C=0.8" means (overall cache capacity)/(overall request range)= 0.8)
"no group"is shown as the largest "group size", which equals to overall number of nodes.

3) Reduction in network delay to computation when sharing within a group vs, when retrieving from a data store

not done yet

* files location
configure files in ./simulation/set1/


* result location
./simulation/set1/plots..../


* Run Simulation:
sh ./simulation/set1/run.sh

* more detail
please read ./simulation/set1/README.md


* publication:
```
Nitinder Mohan, Pengyuan Zhou, Keerthana Govindaraj, and Jussi Kangasharju. 2017. 
Managing Data in Computational Edge Clouds. 
In Proceedings of the Workshop on Mobile Edge Communications (MECOMM ’17). 
Association for Computing Machinery, New York, NY, USA, 19–24. 
DOI:https://doi.org/10.1145/3098208.3098212
```

