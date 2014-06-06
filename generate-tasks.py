#!/usr/bin/python
"""
Copyright (c) 2014 High-Performance Computing and GIS (HPCGIS) Laboratory. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
Authors and contributors: Eric Shook (eshook@kent.edu)
"""


import os
import re
import glob
import sys,getopt

'''
The generate tasks script will read the subexperiment.* files in the current working directory and:
 1. create a tasks directory
 2. create a series of tasks one per experiment file 
'''

# Global variables

# This function handles executing a task defined by a taskfile
def createtasklist(tasklistfile,tasklist):

    print " Creating",tasklistfile

    with open(tasklistfile,'w') as f:
        for task in tasklist:
            f.write(task+"\n")

# This function handles executing a task defined by a taskfile
def createtask(taskfile,expfile,runabmexec,netlogomodel,numberofthreads,numberofjobs,tasklists,tasklistindex):
    #execname,params):

    print " Creating",taskfile,"from",expfile,"using",numberofthreads,"threads"

    '''
    program: /path/to/executable_with_a_name 
    parameters: param1 -Optionalconfiguration param2 -AnotherParameter
    '''

    with open(taskfile,'w') as f:
        #<NETLOGO MODEL FILE> <EXPERIMENT FILE> <EXPERIMENT NAME> <NUMBER OF THREADS>
        f.write("program: "+runabmexec+"\n")
        experimentname=expfile.split(".")[-2].strip() 
        paramstring=netlogomodel+" "+expfile+" "+experimentname+" "+str(numberofthreads)+"\n"
        f.write("parameters:"+paramstring)

    print "tasklistindex",tasklistindex
    tasklists[tasklistindex].append(taskfile)

    print tasklists

# Main program code
def main():

    try:
        opts,args=getopt.getopt(sys.argv[1:],"r:m:n:d:j:",["runabmexec=","model=","num=","dir=","jobs="])
    except getopt.GetoptError:
        print "generate-tasks.py -m <netlogo model> -r <runabmexec> -n <number of threads per task> -d <workflow directory> -j <number of jobs>"
        sys.exit(1)

    runabmexec=""
    netlogomodel=""
    workflowdir=""
    numberofthreads=0
    numberofjobs=0
    err=0
    for opt, arg in opts:
        if opt in ("-n", "--num"):
            numberofthreads=int(arg)
        if opt in ("-m", "--model"):
            netlogomodel=arg
        if opt in ("-r", "--runabmexec"):
            runabmexec=arg
        if opt in ("-d", "--dir"):
            workflowdir=arg
        if opt in ("-j", "--jobs"):
            numberofjobs=int(arg)
    if numberofthreads<=0:
        print " [ ERROR ] Number of threads per task must be greater than 0"
        err=1
    if runabmexec=="":
        print " [ ERROR ] Must assign runabmexec"
        err=1
    if netlogomodel=="": 
        print " [ ERROR ] Must assign a netlogo model"
        err=1
    if workflowdir=="": 
        print " [ ERROR ] Must assign a workflow directory"
        err=1
    if numberofjobs<=0: 
        print " [ ERROR ] Number of jobs must be greater than 0" 
        err=1

    print "Number of threads per task",numberofthreads
    print "Number of jobs",numberofjobs

    if err==1:
        print "generate-tasks.py -m <netlogo model> -r <runabmexec> -n <number of threads per task> -d <workflow directory> -j <number of jobs>"
        sys.exit(1)

    print "Starting to generate tasks"

    tasklists=[]
    tasklistindex=0
    print "tasklists",tasklists
    tasklists=[[] for i in range(numberofjobs)]
    print "tasklists",tasklists

    pworkflowdir="."
    os.chdir(pworkflowdir)

    print "Current working directory :",os.getcwd()

    print "Creating tasks directory"
    tasksdir = workflowdir+'/tasks/'
    if not os.path.exists(tasksdir):
       os.mkdir(tasksdir)

    print "Creating tasks in",tasksdir
    print "dir",workflowdir+"/subexperiment.*"
    #taskfiles = os.listdir(tasksdir) # Contains a list of task files to process 
    expfiles = glob.glob(workflowdir+"/subexperiment.*") 
    expfiles.sort()

    print expfiles


    expcount=1
    for expfile in expfiles:
        taskfile=tasksdir+"1."+str(expcount)+".txt"
        createtask(taskfile,expfile,runabmexec,netlogomodel,numberofthreads,numberofjobs,tasklists,tasklistindex)
        tasklistindex=(tasklistindex+1)%numberofjobs
        expcount+=1

    print "Finished generating tasks"

    print "Starting to generate task lists"

    print "Creating tasklists directory"
    tasklistsdir = workflowdir+'/tasklists/'
    if not os.path.exists(tasklistsdir):
       os.mkdir(tasklistsdir)

    for i in range(numberofjobs):
        tasklist=tasklists[i]
        createtasklist(tasklistsdir+"tasklist"+str(i)+".txt",tasklist)


# Run main
if __name__=="__main__":
   main()

