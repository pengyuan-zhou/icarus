#!/bin/sh

# Enable command echo
set -v

#timestamp
current_time=$(date "+%Y.%m.%d-%H.%M.%S")
echo "Current time: $current_time"

# Directory where this script is located
CURR_DIR=`pwd`

# Icarus main folder
ICARUS_DIR=${CURR_DIR}/../..

# Dir where plots will be saved 
plots_folder="plots".$current_time
PLOTS_DIR=${CURR_DIR}/$plots_folder
#mkdir $PLOTS_DIR

# Config file
CONFIG_FILE=${CURR_DIR}/config_cachesize.py

# FIle where results will be saved
RESULTS_FILE=${CURR_DIR}/jussi30results_cachesize.2017.03.29-19.12.02.pickle 
#results_cachesize.$current_time.pickle
#touch $RESULTS_FILE

# Add Icarus code to PYTHONPATH
export PYTHONPATH=${ICARUS_DIR}:$PYTHONPATH

# Run experiments
#echo "Run experiments"
#python ${ICARUS_DIR}/icarus.py --results ${RESULTS_FILE} ${CONFIG_FILE}

# Plot results
echo "Plot results"
python ${CURR_DIR}/plotresults_cachesize.py --results ${RESULTS_FILE} --output ${PLOTS_DIR} ${CONFIG_FILE} 

