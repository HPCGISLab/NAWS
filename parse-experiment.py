#!/usr/bin/python
"""
Copyright (c) 2014 High-Performance Computing and GIS (HPCGIS) Laboratory. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
Authors and contributors: Eric Shook (eshook@kent.edu)
"""

import sys,getopt
from xml.dom import minidom
import itertools
from collections import defaultdict
import math

# Example
# ./parse-experiment.py -m Ache-v1.1b-test2.nlogo -e experiment60a

# Parse out the 'experiments' section of a NetLogo model, ignoring the rest of the file
# It isn't pretty, but it is functional in parsing a NetLogo model
def parseexperiment(f):
    print " Parsing experiment"

    exptext=""
    inexperiments=0
    for line in f:
        if line=="<experiments>\n":
            inexperiments=1

        # Record the conents if within the experiment tags
        if inexperiments==1:
            exptext+=line

        if line=="</experiments>\n":
            inexperiments=0
            break
    return exptext

# From an xml.dom experiment write it to a file with the appropriate header/footer
# to be used by NetLogo to execute a sub-experiment
def writeexperimentfile(experiment,subexperimentdirectory):
    # Print the experiment file to XML
    experimentfilename=subexperimentdirectory+"/subexperiment."+experiment.attributes["name"].value+".xml"
    f=open(experimentfilename,'w')
    f.write("<?xml version=\"1.0\" encoding=\"us-ascii\"?>\n<!DOCTYPE experiments SYSTEM \"behaviorspace.dtd\">\n<experiments>\n")
    f.write(experiment.toxml())
    f.write("\n</experiments>\n")
    f.close()

# Transform a dictionary of enumerated value sets to XML and add to the experimentmaster xml.dom to create a subexperiment
def createexperiment(dict,experimentmaster,experimentgroupcount):
    # Define a new experiment based on master and append to the name the experimentgroup count for a unique name
    experiment=experimentmaster.cloneNode(True) # Duplicate master
    experiment.attributes["name"].value+=str(experimentgroupcount)
    for attr in dict: # Iterate over the dictionary and add values based on attribute variable names
        string=" \n <enumeratedValueSet variable=\""+attr+"\">\n" 
        for value in set(dict[attr]): # Remember each attribute in the dict holds a list of values, set returns unique values in the list
            string+=" <value value=\""+value+"\"/>\n" 
        string+="</enumeratedValueSet> \n "
            
        #print "string=",string
        evsnode=minidom.parseString(string).firstChild # Extract out the XML from the dom
        #print evsnode.toxml()
        experiment.appendChild(evsnode) # Add it to the larger subexperiment
    return experiment

# Parse the xml from the experiment text and create a list of lists of unique simulations in the experiment
def generateexperiments(exptext,experimentname,numberofsubexperiments,subexperimentdirectory):

    print " Generating experiments"

    # Parse experiments XML from netlogo model
    dom=minidom.parseString(exptext)

    # Store subexperiments in a list of lists
    experimentlistoflists=[]

    experimentfound=0

    # This loop iterates over each experiment looking for the user selected experiment (experimentname)
    numberofexperiments=1
    for node in dom.getElementsByTagName('experiment'):
        if node.attributes["name"].value==experimentname: # Experiment found
            experiment=node.cloneNode(True) # Save this experiment
            numberofrepetitions=int(node.attributes["repetitions"].value) # Save the number of repititions for each parameter combination
            print " Experiment %s found (number of repetitions=%i)"%(experimentname,numberofrepetitions)
            experimentfound=1

            # Iterate over each enumeraed value set to find all parameter combinations
            for evs in node.getElementsByTagName('enumeratedValueSet'):
                evslist=[]
                #print "enumeratedValueSet=",evs.attributes["variable"].value
                count=0
                for val in evs.getElementsByTagName('value'): # for each parameter value
                    #print "val", val.attributes["value"].value
                    count+=1                                  # count it
                    #                                         # and add it to the list of parameter combinations 
                    evslist.append((evs.attributes["variable"].value,val.attributes["value"].value))
                #print "count=",count
		numberofexperiments*=count
                # add this value set list to the experiment list (creating a list of lists)
                experimentlistoflists.append(evslist)
            #print node.toxml()
    if experimentfound==0:
       print " [ ERROR ] Experiment",experimentname,"not found"
       exit(1)
    print "The total number of simulations is",numberofexperiments*numberofrepetitions

    # Sort the list so try to align similar experiments
    experimentlistoflists.sort()
    #print experimentlistoflists

    # this function will take the list of lists generated above (experimentlistoflists)
    # which consists of all of the enumeratedvaluesets with their individual values
    # and creates unique combinations of the parameters
    # this new list of lists is saved in allexperiments
    # allexperiments represents every single simulation parameter configuration in a defined experiment
    allexperiments=itertools.product(*experimentlistoflists)

    # Count using loop (len would be simpler) 
    count=0
    for simulation in allexperiments:
        count+=1

    print "The total number of experiments generated is",count

    # Remove all enumerated value sets from experiment (which are grouped currently)
    # This is necessary, because we will add them back one at a time to represent a single sub-experiment
    for evs in experiment.getElementsByTagName('enumeratedValueSet'):
        experiment.removeChild(evs)
        evs.unlink()
    #print experiment.toxml()
    experimentmaster=experiment.cloneNode(True)

    # Build a set of sub-experiment (xml) files that are grouped by attributevaluesets
    # It is controllable how 

    simulationcount=0 # This parameter counts the number of simulations 

    # This parameter enables multiple simulations (parameter combinations) to be combined into a single xml file
    # rather than having each one run separately

    # Determine how large sub-experiments should be
    experimentgroupsize=int(math.ceil(float(count)/float(numberofsubexperiments)))
    experimentgroupcount=0 # This parameter counts the number of experiment groups

    dict=defaultdict(list)

    # Re-create allexperiments
    allexperiments=itertools.product(*experimentlistoflists)
    for simulation in allexperiments:
        simulationcount+=1
        for evs in simulation:
            #print "evs=",evs
            val=evs[1] # Pull the value from the attribute/value pair
            val=val.replace("\"","&quot;") # NetLogo handles strings using HTML formatting, but Python auto-changes them upon read
            attribute=evs[0]
            dict[attribute].append(val)
            #print "val=",val
       #print "sim=",simulation
        if(simulationcount%experimentgroupsize==0): # We reached out experiment group size limit, so write out the results
            #experiment=createexperiment(dict,experimentmaster,experimentgroupcount)
            experiment=createexperiment(dict,experimentmaster,simulationcount) # Create a DOM based on the dictionary that can be written

            writeexperimentfile(experiment,subexperimentdirectory)
            # Now that an experiment group has been written setup a new experiment for writing
            # Increase count, define a new experiment based on master and append to the name the experimentgroup count for a unique name
            experimentgroupcount+=1
            #experiment=experimentmaster.cloneNode(True)
            #experiment.attributes["name"].value+=str(experimentgroupcount)
            dict=defaultdict(list) # Reset the dictionary too

    # Check to see if any remaining simulations have not been written (it will be a smaller experiment as it has not reached groupsize level
    # This happens if allexperiments is not divisible by experimentgroupsize 
    if(simulationcount%experimentgroupsize!=0):
        # Write the remaining experiments
        experiment=createexperiment(dict,experimentmaster,experimentgroupcount)
        writeexperimentfile(experiment,subexperimentdirectory)
        experimentgroupcount+=1
        dict=defaultdict(list) # Reset the dictionary too

    #print "#####################################################"

    #print experiment.toxml()
    #print experiment.toprettyxml(indent='  ',newl='')

    # FIXME: Catch the end experiment if it is not modulus of groupsize

    print "Simulation group files written :",experimentgroupcount

def main():
    # Try to extract command-line options
    try:
        opts,args=getopt.getopt(sys.argv[1:],"m:e:n:d:",["model=","experiment=","num=","dir="])
    except getopt.GetoptError:
        print "parse-experiment.py -m <netlogomodel.nlogo> -e <experiment-name> -n <number of sub-experiments> -d <directory for sub-experiments>" 
        sys.exit(1)

    # Set model filename and experiment name based on command-line parameter
    modelfilename=""
    experimentname=""
    subexperimentdirectory=""
    numberofsubexperiments=0
    for opt, arg in opts:
        if opt in ("-m", "--model"):
            modelfilename=arg
        if opt in ("-e", "--experiment"):
            experimentname=arg
        if opt in ("-n", "--num"):
            numberofsubexperiments=int(arg)
        if opt in ("-d", "--dir"):
            subexperimentdirectory=arg
    err=0
    if modelfilename=="":
        print " [ ERROR ] No model file found"
        err=1
    if experimentname=="":
        print " [ ERROR ] No experiment found"
        err=1
    if subexperimentdirectory=="":
        print " [ ERROR ] No subexperiment directory"
        err=1
    if numberofsubexperiments<=0:
        print " [ ERROR ] Number of subexperiments must be greater than 0"
        err=1
    if err==1:
        print "parse-experiment.py -m <netlogomodel.nlogo> -e <experiment-name> -n <number of sub-experiments> -d <directory for sub-experiments>" 
        sys.exit(1)
    print "Start parsing netlogo model file %s"%modelfilename
    print "Experiment %s"%experimentname
    print "Number of sub experiments to generate",numberofsubexperiments
    print "Directory for subexperiments",subexperimentdirectory
    # Now I have a netlogo model filename and experiment to parse
    # Try to open the file and parse 
    try:
        f=open(modelfilename)
        exptext=parseexperiment(f)
        f.close()
    except IOError:
        print ' [ ERROR ] Cannot open file %s'%modelfilename
        sys.exit(1)

    # Generate the job files after decomposing the experiment 
    generateexperiments(exptext,experimentname,numberofsubexperiments,subexperimentdirectory)


# Run main
if __name__=="__main__":
   main()
