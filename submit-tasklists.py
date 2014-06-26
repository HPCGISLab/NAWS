#!/usr/bin/python
"""
Copyright (c) 2014 High-Performance Computing and GIS (HPCGIS) Laboratory. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
Authors and contributors: Eric Shook (eshook@kent.edu)
"""

import os
import re
import glob
import subprocess

import sys,getopt

'''
1. For each tasklist, create a job submission script
2. The job submission script should launch the ABM workflow with a single tasklist
3. Submit each script to the job queue system
'''

# This function handles creation of a job submission script for a tasklist 
def createsubmitscript(submitfile,tasklistfile,workflowexec,numberofthreads,execdir):
    #execname,params):

    print " Creating",submitfile,"for",tasklistfile,"that will launch",numberofthreads,"threads","in directory:",execdir

    with open(submitfile,'w') as f:
        submitfile="""#!/bin/bash

#PBS -l ncpus=16

#PBS -l walltime=10:00:00
#PBS -j oe
#PBS -q batch
##PBS -q debug
#PBS -W group_list=at3uuhp
#PBS -M eshook@kent.edu

#set -x

echo " [ STARTING JOB ]"
ja 
date

"""
        f.write(submitfile)
        execdirstr="cd "+execdir+"\n\n"
        f.write(execdirstr)
        execstr="time "+workflowexec+" -t "+tasklistfile+" -n "+str(numberofthreads)
        f.write(execstr)
        f.write("\n\nja -chlst\n\necho \ndate\necho \" [ FINISHED JOB ]\"\n")

# Main program code
def main():


    try:
        opts,args=getopt.getopt(sys.argv[1:],"w:d:n:e:",["workflowxec=","dir=","num=","execdir="])
    except getopt.GetoptError:
        print "submit-tasklists.py -w <workflow.py path> -d <workflow directory> -n <number of threads> -e <exec dir>"
        sys.exit(1)

    execdir=""
    workflowexec=""
    workflowdir=""
    numberofthreads=0
    err=0
    for opt, arg in opts:
        if opt in ("-n", "--num"):
            numberofthreads=int(arg)
        if opt in ("-w", "--workflowxec"):
            workflowexec=arg
        if opt in ("-d", "--dir"):
            workflowdir=arg
        if opt in ("-e", "--execdir"):
            execdir=arg
    if numberofthreads<=0:
        print " [ ERROR ] Number of threads per task must be greater than 0"
        err=1
    if workflowexec=="":
        print " [ ERROR ] Must assign workflowexec"
        err=1
    if workflowdir=="": 
        print " [ ERROR ] Must assign a workflow directory"
        err=1
    if execdir=="": 
        print " [ ERROR ] Must assign an exec directory"
        err=1

    print "Number of threads per task",numberofthreads

    if err==1:
        print "submit-tasklists.py -w <workflow.py path> -d <workflow directory> -n <number of threads> -e <exec dir>"
        sys.exit(1)

    print "Starting to generate submit scripts"

    pworkflowdir="."
    os.chdir(pworkflowdir)

    print "Current working directory :",os.getcwd()

    print "Creating submit-scripts directory"
    submitdir = workflowdir+'/submit-scripts/'
    if not os.path.exists(submitdir):
       os.mkdir(submitdir)

    print "Creating submit scripts in",submitdir
    tasklistfiles = glob.glob(workflowdir+"/tasklists/*") 
    tasklistfiles.sort()

    print tasklistfiles



    submitfiles=[]

    for tasklistfile in tasklistfiles:
        baselistname=os.path.basename(tasklistfile)
        submitfile=submitdir+"submit-"+baselistname+".sh"
        submitfiles.append(submitfile)
        createsubmitscript(submitfile,tasklistfile,workflowexec,numberofthreads,execdir)

    # Submit the scripts
    for submitfile in submitfiles:
        returncode=subprocess.check_call("echo not really submitting - qsub "+submitfile,shell=True)
        print "Submitted",submitfile,"with return code =",returncode

# Run main
if __name__=="__main__":
   main()

