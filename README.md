NetLogo ABM Workflow System (NAWS) 
===

Introduction
---
NetLogo is a widely used agent-based modeling environment (http://ccl.northwestern.edu/netlogo/index.shtml), but lacks support for scalable parallel execution.
The NetLogo ABM Workflow System (NAWS) automatically decomposes large NetLogo ABM experiments defined using BehaviorSpace into multiple sub-experiments and executes them in parallel using one or more nodes.
While BehaviorSpace supports multi-core parallelism it has been found to scale relatively poorly.
NAWS divides the parameter space of a large experiment into multiple sub-experiments to be executed on one or more nodes without modification to a NetLogo ABM.

Installation
---

1. Copy files into a directory such as ~/workflow/bin

2. Change file modes to be executable

chmod 755 ~/workflow/bin/*.py
chmod 755 ~/workflow/bin/*.sh

3. Modify system-level configuration files
   - Open runexperiment.sh and modify parameters based on system configuration
   - Open submit-tasklists.sh and modify submission script to match batch job management system
   - Open runabm and configure memory requirements if executing a particularly complex NetLogo model

Example
---
4. Enter into a directory with a NetLogo model with defined experiment

5. Execute the NAWS using ~/workflow/bin/run/runexperiment.sh <Netlogo model name> <Experiment name>
   A new directory containing all of the parameter files and sub-experiment information will be created along with multiple table files containing the results of each sub-experiment

