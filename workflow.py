#!/usr/bin/python
"""
Copyright (c) 2014 High-Performance Computing and GIS (HPCGIS) Laboratory. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
Authors and contributors: Eric Shook (eshook@kent.edu)
"""

import os
import datetime
import time
import re
import subprocess
from Queue import Queue
#from threading import Thread
import threading
import sys,getopt

'''
The workflow script accepts a tasklist file, which contains a list of taskfiles.
A task may represent a simulation of an ABM or climate model. Tasks can be run 
simultaneously if there are no dependencies or ordered in the case of 
dependencies. Tasks may also include pre-processing or post-processing tasks.
'''

# TODO: Logging may be useful if the workflow becomes long

# TODO: Currently num_threads is user-defined, which controls the number of threads to launch tasks
#       However, it would be better to include in the taskfile the number of cores needed
#       and define the number of cores available, enabling the workflow system to manage core allocation

# Global variables

# The number of threads used to handle tasks is passed as a parameter
num_threads=0

# Array of threads (so they can be killed if needed)
threads=[]

# Array of task workflow numbers (one per thread/worker)
threadtasknums=[]

# Task queue
taskqueue=Queue()

# This function handles executing a task defined by a taskfile
def runtask(taskfile):

    # Read and parse the taskfile with the following format
    # Note additional parameters will likely be added based on need (e.g., CWD, data-dir)
    '''
    program: /path/to/executable_with_a_name 
    parameters: param1 -Optionalconfiguration param2 -AnotherParameter
    '''
    with open(taskfile,'r') as f:
        # Set the required parameters as None for error checking at the end
        program=None
        parameters=None
        for line in f:
            if line.startswith("program:"):
                # Extract the entire program location from after the colon split()[1]) with whitespace removed (strip())
                program=line.split(":",1)[1].strip() 
                #print "Program="+program
          
            if line.startswith("parameters:"):
                # Extract the parameter string from after the colon split()[1]) with whitespace removed (strip())
                parameters=line.split(":",1)[1].strip() 
                #print "Parameters="+parameters

        # Error checking for required parameters
        if program==None:
            raise Exception("program missing in taskfile",taskfile) 
        if  parameters==None:
            raise Exception("parameters missing in taskfile",taskfile) 

        print "Calling program="+program,parameters
        '''
        In future versions that have defined input,output,stdout,etc.
        there could be more logic here to:
            - run each model in a defined directory
            - output stdout,stderr in the directory
            - package up output files for easier transfer
            - ...
        '''
        returncode=subprocess.check_call(program+" "+parameters,shell=True)

# A task worker loops while there are tasks left in the taskqueue
# Input parameter is a thread id (tid)
def taskworker(tid):
    while not taskqueue.empty():
        taskfile=taskqueue.get()

        tasknum=taskfile.split("/",1)[1].split(".",1)[0].strip() 
        tasknum=re.sub("\D", "", tasknum)
        #print "tid=",tid
        threadtasknums[tid]=int(tasknum)

        # While there is a dependency problem (lower order task numbers are still being processed)
        # then spintwait
        mintasknum=min(threadtasknums)
        while threadtasknums[tid]>mintasknum:
            #print "min=",minthreadtasknum,"min(array)=",min(*threadtasknums),"nums[",i,"]=",threadtasknums[i]
            #if(threadtasknums[tid]<=min(*threadtasknums)): # If this task number is less than or equal to the minimum 
            #    break # then there are no dependencies, so you can break out of this infinite loop
            time.sleep(1)  # this is a spin-wait loop
            mintasknum=min(*threadtasknums)

        print "Thread",tid,"running",taskfile,"at",str(datetime.datetime.now())
        try:
            runtask(taskfile)
        except:
            exit(1)
        taskqueue.task_done()
    threadtasknums[tid]=999999 # Set the tasknum for tid to 9999 so it doesn't influence dependencies
    print "Thread",tid,"quitting, because taskqueue is empty"

# Main program code
def main():
    print "Starting node workflow"

    try:
        opts,args=getopt.getopt(sys.argv[1:],"n:t:",["numthreads=","tasklist="])
    except getopt.GetoptError:
        print "workflow.py -n <number of threads to launch> -t <tasklistfile>"
        sys.exit(1)

    # Set model filename and experiment name based on command-line parameter
    num_threads=0
    tasklistfile=""
    for opt, arg in opts:
        if opt in ("-n", "--numthreads"):
            num_threads=int(arg)
        if opt in ("-t", "--tasklist"):
            tasklistfile=arg
    err=0
    if num_threads<=0:
        print " [ ERROR ] Number of threads must be greater than 0"
        err=1
    if tasklistfile=="":
        print " [ ERROR ] Must provide tasklistfile"
        err=1
    if err==1:
        print "workflow.py -n <number of threads to launch> -t <tasklistfile>"
        sys.exit(1)

    print "Executing in current directory :",os.getcwd()

    print "Reading tasklist file"
    with open(tasklistfile,'r') as f:
        taskfiles = f.readlines()
        f.close()


#    tasksdir = 'tasks/'
#    taskfiles = os.listdir(tasksdir) # Contains a list of task files to process 
    taskfiles.sort()

    print "Starting task queue"
    for taskfile in taskfiles:
        taskqueue.put(taskfile.strip())
    print "Task queue contains ",taskqueue.qsize()," tasks"

    # Start the workflow engine
    # Currently the logic is simple -> one task==one thread==one core but that will need
    # to be modified to account for multithreaded models (agent-based and climate)
    # so eventually this will need to parse the task to determine the number of cores
    # needed by the task and dynamically manage the number of tasks running simultaneously
    print "Starting ",num_threads," threads"
    for i in range(num_threads):
        threadtasknums.append(-1)
        t=threading.Thread(target=taskworker,args=(i,))
        t.daemon=True
        t.setDaemon(True)
        t.start()
        threads.append(t)

    # Now we wait until all of the tasks are finished.
    print "Waiting for threads to finish"

    # Normally you can use a blocking .join, but then you cannot kill the process
    # So instead we spin-wait and catch ^C so a user can kill this process.
#    while threading.activeCount() > 0:
#        time.sleep(20)
    while taskqueue.qsize()>0:
        time.sleep(1)
        print "taskqueue size",taskqueue.qsize()
        ''' # FIXME: Need to clean up this code, which was used for testing ^C 
        try:
            time.sleep(5) # Wait 5 seconds before checking again
                          # FIXME: In production this should be changed to 30
        # If Ctrl+C or other error, kill all of the threads
        except:
            while not taskqueue.empty(): # Empty the queue
                taskqueue.get()
            for i in threads:
                i.kill_received=True
                i.kill()
            exit(1)
        '''

    print "Joining taskqueue"
    # At this point all of the tasks should be finished so we join them
    notfinished=1
    while notfinished==1:
        notfinished=0
        for i in range(num_threads):
            if threadtasknums[i]<999999:
                notfinished=1
                time.sleep(1)
    #while not taskqueue.join(1):
    #    time.sleep(1)
    print "Finished node workflow"

# Run main
if __name__=="__main__":
   main()

