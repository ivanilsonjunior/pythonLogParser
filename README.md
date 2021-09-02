# Cooja log Parser

Another Log Parser for Contiki-NG Experiments.
**Based on [examples/benchmarks/result-visualization](https://github.com/contiki-ng/contiki-ng/tree/develop/examples/benchmarks/result-visualization)**, the program uses the same node.c

## What it do:
- Controls the Cooja's Experiments
- Runs Cooja on non-GUI mode
- Uses the based example node.c as mote. (node.c create)
- Needs autentication for some tasks (admin:letmein)
- After the run, the log is parsed to an ORM
- Metrics and network behaviour could be extracted from ORM

## Classes
### [Runner.py](https://github.com/ivanilsonjunior/pythonLogParser/blob/main/Runner.py)
It's responsible for calling Cooja and running the experiments, could easily used for calling the Cooja by other projects. It is an encapsulated version of [run-cooja.py](https://github.com/contiki-ng/contiki-ng/blob/develop/examples/benchmarks/result-visualization/run-cooja.py)
### [api.py](https://github.com/ivanilsonjunior/pythonLogParser/blob/main/api.py)
It's responsible for presenting experiments, their runs and generated data. It was made in Flask and the user can create new simulations and runs. The generated information is presented by layer.
### [Model.py](https://github.com/ivanilsonjunior/pythonLogParser/blob/main/Model.py)
It's responsible for processing all the things. It's my trying to devel using the Object Oriented paradigm.
TODO: Split apart the data from the presentation

## Install and Run

I've tested on Debian 10 and default-jdk

1. Inside the [Contiki-NG](https://github.com/contiki-ng/contiki-ng) examples folder clone this repository
   1. The JAVA_HOME variable must be setted
2. After the clonning part execute '''python3 -m pip install -r requirements.txt'''
3. Inside the created folder execute the API 'python3 api.py'
   - At the first run a SQLite DB Metrics.db will be created
   - You should access the page via browser (http://localhost:5000) and add an experiment (Click on 'Add Experiment' link and put any name and the Simulation file puts Sim.csc)
   - Inside the experiment page click on new Run
   - After the done you can extract the metrics from run
 
 ### Command-Line
 1. You can use ipython:
   ```
   load Model.py
   exp = Experiment(name = "Test Experiment", experimentFile = "Metrics25m2Node.csc")
   db.add(exp)
   db.commit() # After that yor have a saved experiment and you could run
   exp.runs # List of run linked to that experiment
   exp.run() # Run the Experiment
   r = exp.runs[0] # Gets the first run
   r = db.query(Run).filter_by(id=1).first() # Returns the id 1 run
   r.records # Shows the run record list
   len(db.query(Record).filter_by(run = r).filter_by(node = 2).filter_by(recordType = "TSCH").all()) # Shows the quantity of TSCH records from node 2
   ```


**Due to my programming skills limitation I've decided to write the "_FrontEnd_" using Jinja Templates over Flask**
