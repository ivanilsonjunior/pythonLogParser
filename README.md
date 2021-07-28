# Cooja log Parser

Another Log Parser for Contiki-NG Experiments.
**Based on [examples/benchmarks/result-visualization](https://github.com/contiki-ng/contiki-ng/tree/develop/examples/benchmarks/result-visualization)**

## What I did:
- Controls the Cooja's Experiments
- Runs Cooja on non-GUI mode
- Uses the based example node.c as mote
- Needs autentication for some tasks (admin:letmein)
- After the run, the log is parsed to an ORM
- Metrics and network behaviour could be extracted from ORM

## Install and Run
1. Inside the [Contiki-NG](https://github.com/contiki-ng/contiki-ng) examples folder clone this repository
2. Inside the created folder execute the API 'python3 api.py'
   - At the first run a SQLite DB Metrics.db will be created
   - You should access the page via browser (http://localhost:5000) and add an experiment (Click on 'Add Experiment' link and put any name and the Simulation file puts Sim.csc)
   - Inside the experiment page click on new Run
   - After the done you can extract the metrics from run


**Due to my programming skills limitation I've decided to write the "_FrontEnd_" using Jinja Templates over Flask**
