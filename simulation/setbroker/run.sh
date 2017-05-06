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
CONFIG_FILE=${CURR_DIR}/config.py

# FIle where results will be saved
#RESULTS_FILE=${CURR_DIR}/results.$current_time.pickle
RESULTS_FILE=${CURR_DIR}/results.2017.05.06-18.25.24.pickle
#touch $RESULTS_FILE

# Add Icarus code to PYTHONPATH
export PYTHONPATH=${ICARUS_DIR}:$PYTHONPATH

# Run experiments
#echo "Run experiments"
#python ${ICARUS_DIR}/icarus.py --results ${RESULTS_FILE} ${CONFIG_FILE}

# Plot results
echo "Plot results"
python ${CURR_DIR}/plotresults.py --results ${RESULTS_FILE} --output ${PLOTS_DIR} ${CONFIG_FILE} 

