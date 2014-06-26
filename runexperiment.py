#!/usr/bin/python
"""
Copyright (c) 2014 High-Performance Computing and GIS (HPCGIS) Laboratory. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
Authors and contributors: Eric Shook (eshook@kent.edu)
"""

import getopt,sys
import os
import time
import subprocess
import shutil

def main(): 


    print 'Welcome to NetLogo ABM Workflow System (NAWS)'


    # Parsing command-line parameters
    try:
        opts,args=getopt.getopt(sys.argv[1:],"m:e:",["model=","experiment="])
    except getopt.GetoptError:
        print "runexperiment.py -m <NetLogo model> -e <Experiment name in model>"
        sys.exit(1)

    # Blank names by default for sanity check
    model_name=""
    experiment_name=""
    for opt, arg in opts:
        if opt in ("-m", "--model"):
            model_name=arg
        if opt in ("-e", "--experiment"):
            experiment_name=arg
    err=0
    if model_name=="": 
        print " [ ERROR ] Must provide a NetLogo model"
        err=1
    if experiment_name=="":
        print " [ ERROR ] Must provide an Experiment"
        err=1
    if err==1:
        print "runexperiment.py -m <NetLogo model> -e <Experiment name in model>"
        sys.exit(1)

    # How many subexperiments should be assigned to a "thread group" (defined below)
    subexperiments_per_threadgroup=2

    # How many threads should be used for each subexperiment (referred to a "threadgroup" above)
    # 4-8 have been found to be good on several platforms
    threads_per_subexperiment=8

    # How many cores are available per node
    cores_per_node=16

    # How many jobs should be submitted to the queue system (e.g., qsub)
    number_of_jobs=1

    # Based on the parameters provided above, calculate the number of subexperiments to create
    #NUMBEROFSUBEXPERIMENTS=$((SUBEXPERIMENTSPERTHREADGROUP*NUMBEROFJOBS*(CORESPERNODE/THREADSPERSUBEXPERIMENT)))
    number_of_subexperiments=subexperiments_per_threadgroup*number_of_jobs*(cores_per_node/threads_per_subexperiment)

    print "Executing in current directory :",os.getcwd()
    exec_dir=os.getcwd()
    workflow_bin="~/workflow/bin"
    workflow_bin="~/code/workflow.github/NAWS"

    try:
        os.chdir(exec_dir)
    except:
        print " [ ERROR ] Problem trying to change into the exec_dir:",exec_dir
        sys.exit(1)

    time_of_launch = time.strftime("%Y-%m-%d-%H-%M-%S")

    # Set the workflow directory as a combination of model, experiment, time, and process ID of NAWS
    workflow_dir=exec_dir+"/experiments/"+model_name+"."+experiment_name+"."+time_of_launch+"."+str(os.getpid())

    # Create the workflow directory
    os.makedirs(workflow_dir)

    
    # Copy the model to the working directory as a backup for provenance
    shutil.copy(model_name,workflow_dir)

    # Print out parameters for record keeping
    print " [ MODEL FILE               :",model_name,"]"
    print " [ EXPERIMENT NAME          :",experiment_name,"]"
    print " [ WORKFLOW DIRECTORY       :",workflow_dir,"]"
    print " [ CORES PER NODE           :",cores_per_node,"]"
    print " [ NUMBER OF SUBEXPERIMENTS :",number_of_subexperiments,"]"
    print " [ THREADSPERSUBEXPERIMENT  :",threads_per_subexperiment,"]"
    print " [ NUMBER OF JOBS           :",number_of_jobs,"]"
    
    # Launch the series of scripts to parse and submit the experiments of the ABM

    # Parse experiment extracts out the experiment description (XML) from the ABM and creates a number of sub-experiments
    status=subprocess.call(workflow_bin+"/parse-experiment.py -d "+workflow_dir+" -m "+model_name+" -e "+experiment_name+" -n "+str(number_of_subexperiments),shell=True)
    if status!=0:
        print " [ ERROR ] Problem running parse-experiment.py"
        sys.exit(1) 
    #$WORKFLOWBIN/parse-experiment.py -d $WORKFLOWDIR -m $MODEL -e $EXPERIMENT -n $NUMBEROFSUBEXPERIMENTS

    # Generate tasks creates one task per sub-experiment for the workflow engine to manage
    status=subprocess.call(workflow_bin+"/generate-tasks.py -d "+workflow_dir+" -m "+model_name+" -r "+workflow_bin+"/runabm.sh -n "+str(threads_per_subexperiment)+" -j "+str(number_of_jobs),shell=True)
    if status!=0:
        print " [ ERROR ] Problem running generate-tasks.py"
        sys.exit(1) 
    #$WORKFLOWBIN/generate-tasks.py   -d $WORKFLOWDIR -m $MODEL -r $WORKFLOWBIN/runabm.sh -n $THREADSPERSUBEXPERIMENT -j $NUMBEROFJOBS 

    status=subprocess.call(workflow_bin+"/submit-tasklists.py -d "+workflow_dir+" -w "+workflow_bin+"/workflow.py -n "+str(threads_per_subexperiment)+" -e "+exec_dir,shell=True)
    if status!=0:
        print " [ ERROR ] Problem running submit-tasklists.py"
        sys.exit(1) 
    # Submit tasklists will create a tasklist for each job based on the number of tasks generated previously and create a job file and submit it
    #$WORKFLOWBIN/submit-tasklists.py -d $WORKFLOWDIR -w $WORKFLOWBIN/workflow.py -n $THREADSPERSUBEXPERIMENT -e $EXECDIR


    print 'Successful exit'
 

# Run main
if __name__=="__main__":
   main()


'''
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
'''
