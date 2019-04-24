#!/usr/bin/env python
"""Plot results read from a result set
"""
from __future__ import division
import os
import collections

import numpy as np
import matplotlib
import matplotlib.pyplot as plt



plt.rcParams['text.usetex'] = False

# Aspect ratio of the output figures
plt.rcParams['figure.figsize'] = 8, 5

# Size of font in legends
LEGEND_SIZE = 14

# Plot
PLOT_EMPTY_GRAPHS = False

# Catalogue of possible bw shades (for bar charts)
BW_COLOR_CATALOGUE = ['k', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9']

# Catalogue of possible hatch styles (for bar charts)
HATCH_CATALOGUE = [None, '/', '\\', '\\\\', '//', '+', 'x', '*', 'o', '.', '|', '-', 'O']


fig = plt.figure()
_, ax1 = plt.subplots()
#if 'title' in desc:
    #plt.title(desc['title'])
plt.xlabel('Content population of shared set', fontsize=20)
plt.ylabel('Internal link load', fontsize=20)
#plt.xscale(desc['xscale'])
#plt.yscale(desc['yscale'])
#if 'xticks' in desc:
#    ax1.set_xticks(desc['xticks'])
#    ax1.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
#    ax1.set_xticklabels([str(xtick) for xtick in desc['xticks']])
#if 'yticks' in desc:
#    ax1.set_yticks(desc['yticks'])
#    ax1.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
#    ax1.set_yticklabels([str(ytick) for ytick in desc['yticks']])

plt.plot([1000,2000,3000,4000,5000,6000,7000,8000,9000,10000], [78.207468,78.080367,77.832072,77.111058,76.92292,76.682050,76.481442,76.422814,76.306591,76.017742], 'g^')


plt.show()
