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
GROUP_STYLE = {
         'GROUP':         'b-o',
         'NOTGROUP':        'g-D'
                }

# This dict maps name of strategies to names to be displayed in the legend
GROUP_LEGEND = {
         'GROUP':           'GROUP',
         'NOTGROUP':        'NOTGROUP'
                    }

# Color and hatch styles for bar charts of cache hit ratio and link load vs topology
GROUP_BAR_COLOR = {
    'GROUP':          'k',
    'NOTGROUP':          '0.4'
    }

STRATEGY_BAR_HATCH = {
    'LCE':          None,
    'LCD':          '//',
    'NO_CACHE':     'x',
    'HR_ASYMM':     '+',
    'HR_SYMM':      '\\'
    }


def plot_cache_hits_vs_cache_size(resultset, topology, cache_size_range, groups, plotdir):
    desc = {}
    desc['title'] = 'Cache hit ratio vs cache size: T=%s ' % (topology)
    desc['ylabel'] = 'Cache hit ratio'
    desc['xlabel'] = 'Cache size'
    desc['xparam'] = ('cache_placement','network_cache')
    desc['xvals'] = cache_size_range
    desc['filter'] = {'topology': {'name': topology}}
    desc['ymetrics'] = [('CACHE_HIT_RATIO', 'MEAN')]*len(groups)
    desc['ycondnames'] = [('group', 'name')]*len(groups)
    desc['ycondvals'] = groups
    desc['errorbar'] = True
    desc['legend_loc'] = 'upper right'
    desc['line_style'] = GROUP_STYLE
    desc['legend'] = GROUP_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    plot_lines(resultset, desc, 'CACHE_HIT_RATIO_VS_CACHE_SIZET=%s.pdf'
               % topology, plotdir)

    

def plot_latency_vs_cache_size(resultset, topology, cache_size_range, groups, plotdir):
    desc = {}
    desc['title'] = 'Latency vs cache Size: T=%s' % (topology)
    desc['xlabel'] = 'Cache size'
    desc['ylabel'] = 'Latency (ms)'
    desc['xparam'] = ('cache_placement','network_cache')
    desc['xvals'] = cache_size_range
    desc['filter'] = {'topology': {'name': topology}}
    desc['ymetrics'] = [('LATENCY', 'MEAN')]*len(groups)
    desc['ycondnames'] = [('group', 'name')]*len(groups)
    desc['ycondvals'] = groups
    desc['errorbar'] = True
    desc['legend_loc'] = 'upper left'
    desc['line_style'] = GROUP_STYLE
    desc['legend'] = GROUP_LEGEND
    desc['plotempty'] = PLOT_EMPTY_GRAPHS
    plot_lines(resultset, desc, 'LATENCY_VS_CACHE_SIZET=%s.pdf'
               % topology, plotdir)


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
    groups = settings.GROUPS
    strategies = settings.STRATEGIES
    # Plot graphs
    for topology in topologies:
        for alpha in alphas:
            logger.info('Plotting cache hit ratio for topology %s vs cache size' % (topology))
            plot_cache_hits_vs_cache_size(resultset, topology, cache_sizes, groups, plotdir)
            
            logger.info('Plotting latency for topology %s vs cache size' % (topology))
            plot_latency_vs_cache_size(resultset, topology, cache_sizes, groups,plotdir)

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
