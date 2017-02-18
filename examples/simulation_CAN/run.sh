#!/bin/sh

# Enable command echo
set -v

# Directory where this script is located
CURR_DIR=`pwd`

# Icarus main folder
ICARUS_DIR=${CURR_DIR}/../..

# Dir where plots will be saved
PLOTS_DIR=${CURR_DIR}/2_12_group_tiscali_2

# Config file
CONFIG_FILE=${CURR_DIR}/config_ranknum_9_9.py

# FIle where results will be saved
#RESULTS_FILE=${CURR_DIR}/9_14_cachesize_rankdiff1_rep10_Tiscali2.pickle
RESULTS_FILE=${CURR_DIR}/9_14_ranknum_cache0.001_rankdiff1_rep30_Tiscali2.pickle
# Add Icarus code to PYTHONPATH
export PYTHONPATH=${ICARUS_DIR}:$PYTHONPATH

# Run experiments
#echo "Run experiments"
#python ${ICARUS_DIR}/icarus.py --results ${RESULTS_FILE} ${CONFIG_FILE}


# Plot results
echo "Plot results"
python ${CURR_DIR}/plotresults_ranknum.py --results ${RESULTS_FILE} --output ${PLOTS_DIR} ${CONFIG_FILE}
