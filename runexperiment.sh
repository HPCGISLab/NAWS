#!/bin/bash
"""
Copyright (c) 2014 High-Performance Computing and GIS (HPCGIS) Laboratory. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
Authors and contributors: Eric Shook (eshook@kent.edu)
"""

# User defined command-line parameters
MODEL=$1
EXPERIMENT=$2

# Sanity check command-line parameters
[ -z "$EXPERIMENT" ] && echo " [ ERROR ] Missing parameters - To run : $0 <netlogo model> <experiment name>" && exit 1
[ ! -e "$MODEL" ]    && echo " [ ERROR ] Netlogo model $MODEL does not exist" && exit 1

# These are configurable  

# How many subexperiments should be assigned to a "thread group" (defined below)
SUBEXPERIMENTSPERTHREADGROUP=2

# How many threads should be used for each subexperiment (referred to a "threadgroup" above)
# 4-8 have been found to be good on several platforms
THREADSPERSUBEXPERIMENT=8

# How many cores are available per node
CORESPERNODE=16

# How many jobs should be submitted to the queue system (e.g., qsub)
NUMBEROFJOBS=1

# Based on the parameters provided above, calculate the number of subexperiments to create
NUMBEROFSUBEXPERIMENTS=$((SUBEXPERIMENTSPERTHREADGROUP*NUMBEROFJOBS*(CORESPERNODE/THREADSPERSUBEXPERIMENT)))

# Environment variables
EXECDIR=$PWD
WORKFLOWBIN=~/workflow/bin



# Setup a unique working directory for workflow using a combination of date, time, and random number
[ ! -e "$EXECDIR" ] && echo " [ ERROR ] EXECDIR $EXECDIR does not exist" && exit 1
cd $EXECDIR
DATESTR=`date +"%m-%d-%y_%I-%M-%p.$$"`

# Set the workflow directory
WORKFLOWDIR=$EXECDIR/experiments/$MODEL.$EXPERIMENT.$DATESTR


# Make the working directory
[ ! -e "experiments" ] && mkdir experiments
mkdir $WORKFLOWDIR

# Copy the model to the working directory as a backup for provenance
cp $MODEL $WORKFLOWDIR

# Print out parameters for record keeping
echo " [ MODEL FILE               : $MODEL ]"
echo " [ EXPERIMENT NAME          : $EXPERIMENT ]"
echo " [ WORKFLOW DIRECTORY       : $WORKFLOWDIR ]"
echo
echo " [ CORES PER NODE           : $CORESPERNODE ]"
echo " [ NUMBER OF SUBEXPERIMENTS : $NUMBEROFSUBEXPERIMENTS ]"
echo " [ THREADSPERSUBEXPERIMENT  : $THREADSPERSUBEXPERIMENT ]"
echo " [ NUMBER OF JOBS           : $NUMBEROFJOBS ]"

# Launch the series of scripts to parse and submit the experiments of the ABM

# Parse experiment extracts out the experiment description (XML) from the ABM and creates a number of sub-experiments
$WORKFLOWBIN/parse-experiment.py -d $WORKFLOWDIR -m $MODEL -e $EXPERIMENT -n $NUMBEROFSUBEXPERIMENTS

# Generate tasks creates one task per sub-experiment for the workflow engine to manage
$WORKFLOWBIN/generate-tasks.py   -d $WORKFLOWDIR -m $MODEL -r $WORKFLOWBIN/runabm -n $THREADSPERSUBEXPERIMENT -j $NUMBEROFJOBS 

# Submit tasklists will create a tasklist for each job based on the number of tasks generated previously and create a job file and submit it
$WORKFLOWBIN/submit-tasklists.py -d $WORKFLOWDIR -w $WORKFLOWBIN/workflow.py -n $THREADSPERSUBEXPERIMENT -e $EXECDIR

