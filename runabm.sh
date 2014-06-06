#!/bin/bash
"""
Copyright (c) 2014 High-Performance Computing and GIS (HPCGIS) Laboratory. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
Authors and contributors: Eric Shook (eshook@kent.edu)
"""

# Enable debugging 
#set -x
#set -v

# User-defined variables
MODEL=$1
EXPERIMENTFILE=$2
EXPERIMENT=$3
THREADS=$4

# Use CWD as the directory of choice

[ -z "$THREADS" ] && echo "To execute: $0 <NETLOGO MODEL FILE> <EXPERIMENT FILE> <EXPERIMENT NAME> <NUMBER OF THREADS>" && exit 1

# System-level variables
# These may need to be modified per installation or new ABMs
# These define the memory requirements for an ABM
export NETLOGO=/usr/local/packages/netlogo-5.0.3
export MEMORY=$((THREADS*512))
export PERMSIZE=$((THREADS*32))
export CODECACHESIZE=$((THREADS*64))

[ $PERMSIZE      -lt 128 ] && export PERMSIZE=128
[ $CODECACHESIZE -lt 256 ] && export CODECACHESIZE=256

# Set jobid as either PBS jobid or PID of script
export JOBID=$PBS_JOBID
[ -z "$JOBID" ] && export JOBID=$$ # Replace PBS job id with own PID

# Sanity check
[ ! -e "$MODEL" ]          && echo "Netlogo model not found : $MODEL"            && exit 2
[ ! -e "$EXPERIMENTFILE" ] && echo "Experiment file not found : $EXPERIMENTFILE" && exit 3 

# Optimizations

# Load latest java module if module command is available
[ ! -z "`which module`" ] && module load java/1.7.0_45-sun

# If google perftools malloc is available, use it.
[ -e "/usr/local/packages/bench/gperftools-2.1/lib/libtcmalloc.so" ] && export LD_PRELOAD="/usr/local/packages/bench/gperftools-2.1/lib/libtcmalloc.so"

# Note: Remember that on certain machines you can over-allocate threads and use hyperthreading

# Ensure extensions are included in the working directory
[ ! -e "extensions" ] && ln -sf $NETLOGO/extensions .

echo -n "Working directory: "
pwd

# Print parameters
echo " [ MODEL : $MODEL ]"
echo " [ EXPERIMENT : $EXPERIMENT ]"
echo " [ THREADS : $THREADS ]"
echo " [ MEMORY ALLOCATED : $MEMORY MB ]"
echo " [ PERMSIZE ALLOCATED : $PERMSIZE MB ]"
echo
echo " [ STARTING ]"

       # Future plans:
       # Test to see if gc is causing performance problems.  If so, then perhaps cut simulations short.
       #-verbose:gc

       # Note: spreadsheet may create memory problems so avoid if possible
       #--spreadsheet out.spreadsheet.$MODEL.$EXPERIMENT.$PBS_JOBID.csv"

# The following parameters were selected to optimize for NetLogo models (specifically the Ache model)
COMMAND="java -server \
       -Dcom.sun.media.jai.disableMediaLib=true
       -Xmx${MEMORY}M \
       -XX:PermSize=${PERMSIZE}m \
       -XX:MaxPermSize=${PERMSIZE}m \
       -XX:ReservedCodeCacheSize=${CODECACHESIZE}m \
       -XX:+UseParallelGC \
       -XX:ParallelGCThreads=${THREADS} \
       -cp .:$NETLOGO/NetLogo.jar \
       org.nlogo.headless.Main \
       --model $MODEL \
       --experiment $EXPERIMENT \
       --setup-file $EXPERIMENTFILE \
       --threads $THREADS \
       --table out.table.$MODEL.$EXPERIMENT.$JOBID.csv" 

echo "Running command : $COMMAND"

time $COMMAND
RET=$?

[ "$RET" != "0" ] && echo " [ ERROR ] Problem running command return code : $RET" && exit 100 

echo " [ FINISHED ]"

