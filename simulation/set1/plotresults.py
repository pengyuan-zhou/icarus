#!/usr/bin/env python
"""Plot results read from a result set
"""
from __future__ import division
import os
import argparse
import collections
import logging

import numpy as np
import matplotlib.pyplot as plt

from icarus.util import Settings, Tree, config_logging, step_cdf
from icarus.tools import means_confidence_interval
from icarus.results import plot_lines, plot_bar_chart
from icarus.registry import RESULTS_READER


# Logger object
logger = logging.getLogger('plot')

# These lines prevent insertion of Type 3 fonts in figures
# Publishers don't want them
plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.use14corefonts'] = True

# If True text is interpreted as LaTeX, e.g. underscore are interpreted as 
# subscript. If False, text is interpreted literally
plt.rcParams['text.usetex'] = False

# Aspect ratio of the output figures
plt.rcParams['figure.figsize'] = 8, 5

# Size of font in legends
LEGEND_SIZE = 14

# Line width in pixels
LINE_WIDTH = 1.5

# Plot
PLOT_EMPTY_GRAPHS = True

# This dict maps strategy names to the style of the line to be used in the plots
# Off-path strategies: solid lines
# On-path strategies: dashed lines
# No-cache: dotted line
RANK_STYLE = {
         4:     'b-o',
         8:     'g-D',
         16:    'm-^',         
         32:    'c-s'
                }

# This dict maps name of strategies to names to be displayed in the legend
RANK_LEGEND = {
         4:         '4 WORKLOADS',
         8:         '8 WORKLOADS',
         16:        '16 WORKLOADS',
         32:        '32 WORKLOADS'
                    }

# Color and hatch styles for bar charts of cache hit ratio and link load vs topology
RANK_BAR_COLOR = {
    4:      'k',
    8:      '0.4',
    16:     '0.5',
    32:     '0.6'
    }

STRATEGY_BAR_HATCH = {
    'LCE':          None,
    'LCD':          '//',
    'NO_CACHE':     'x',
    'HR_ASYMM':     '+',
    'HR_SYMM':      '\\'
    }


def plot_cache_hits_vs_group_size(resultset, topology, cache_size, group_size_range, ranks, plotdir):
    desc = {}
    desc['title'] = 'Cache hit ratio vs Group size: T=%s C=%s' % (topology, cache_size)
    desc['ylabel'] = 'Cache hit ratio'
    desc['xlabel'] = 'Group size'
    desc['xparam'] = ('topology', 'n_member')
    desc['xvals'] = group_size_range
    desc['filter'] = {'topology': {'name': topology},
                      'cache_placement': {'network_cache': cache_size}}
    desc['ymetrics'] = [('CACHE_HIT_RATIO', 'MEAN')]*len(ranks)
    desc['ycondnames'] = [('workload', 'n_rank')]*len(ranks)
    desc['ycondvals'] = ranks
    desc['errorbar'] = True
    desc['legend_loc'] = 'upper right'
    desc['line_style'] = RANK_STYLE
    desc['legend'] = RANK_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    plot_lines(resultset, desc, 'CACHE_HIT_RATIO_VS_GROUP_SIZET=%s@C=%s.pdf'
               % (topology, cache_size), plotdir)

    

def plot_latency_vs_group_size(resultset, topology, cache_size, group_size_range, ranks, plotdir):
    desc = {}
    desc['title'] = 'Latency vs Group Size: T=%s C=%s' % (topology, cache_size)
    desc['xlabel'] = 'Group size'
    desc['ylabel'] = 'Latency (ms)'
    desc['xparam'] = ('topology', 'n_member')
    desc['xvals'] = group_size_range
    desc['filter'] = {'topology': {'name': topology},
                      'cache_placement': {'network_cache': cache_size}}
    desc['ymetrics'] = [('LATENCY', 'MEAN')]*len(ranks)
    desc['ycondnames'] = [('workload', 'n_rank')]*len(ranks)
    desc['ycondvals'] = ranks
    desc['errorbar'] = True
    desc['legend_loc'] = 'upper left'
    desc['line_style'] = RANK_STYLE
    desc['legend'] = RANK_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    plot_lines(resultset, desc, 'LATENCY_VS_GROUP_SIZET=%s@C=%s.pdf'
               % (topology, cache_size), plotdir)


def run(config, results, plotdir):
    """Run the plot script
    
    Parameters
    ----------
    config : str
        The path of the configuration file
    results : str
        The file storing the experiment results
    plotdir : str
        The directory into which graphs will be saved
    """
    settings = Settings()
    settings.read_from(config)
    config_logging(settings.LOG_LEVEL)
    resultset = RESULTS_READER[settings.RESULTS_FORMAT](results)
    # Create dir if not existsing
    if not os.path.exists(plotdir):
        os.makedirs(plotdir)
    # Parse params from settings
    cache_sizes = settings.NETWORK_CACHE
    topologies = settings.TOPOLOGIES
    alphas = settings.ALPHA
    groupsizes = settings.N_SIZES
    strategies = settings.STRATEGIES
    ranks = settings.N_RANKS
    # Plot graphs
    for topology in topologies:
        for alpha in alphas:
            for cache_size in cache_sizes:
                logger.info('Plotting cache hit ratio for topology %s and cache size %s vs alpha' % (topology, str(cache_size)))
                plot_cache_hits_vs_group_size(resultset, topology, cache_size, groupsizes, ranks, plotdir)
                
                logger.info('Plotting latency for topology %s vs cache size %s' % (topology, str(cache_size)))
                plot_latency_vs_group_size(resultset, topology, cache_size, groupsizes, ranks, plotdir)

def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("-r", "--results", dest="results",
                        help='the results file',
                        required=True)
    parser.add_argument("-o", "--output", dest="output",
                        help='the output directory where plots will be saved',
                        required=True)
    parser.add_argument("config",
                        help="the configuration file")
    args = parser.parse_args()
    run(args.config, args.results, args.output)

if __name__ == '__main__':
    main()
