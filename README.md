# Cooja Log Parser

Another Log Parser for Contiki-NG Experiments.
**Based on [examples/benchmarks/result-visualization](https://github.com/contiki-ng/contiki-ng/tree/develop/examples/benchmarks/result-visualization)**, the program uses the same node.c


## What it does:

- Controls Cooja's experiments.
- Runs Cooja in non-GUI mode.
- Retains the generated data.
- Supports bulk runs (multiple runs with a newly generated random seed).
- Utilises the base example node.c as a mote (node.c create).
- Requires authentication for specific tasks (admin:letmein).
- After the run, the log is parsed into an ORM.
- More than 40 metrics and network behaviour can be extracted from the ORM.

## Live Demonstration
You can access a live demo: [http://coimbra.ifrn.edu.br/nalpios/](http://coimbra.ifrn.edu.br/nalpios/) or

You can access a [run example](http://coimbra.ifrn.edu.br/nalpios/run/3)

## Classes
### [Runner.py](https://github.com/ivanilsonjunior/pythonLogParser/blob/main/Runner.py)
It's responsible for calling Cooja, and running the experiments could easily used for calling the Cooja by other projects. It is an encapsulated version of [run-cooja.py](https://github.com/contiki-ng/contiki-ng/blob/develop/examples/benchmarks/result-visualization/run-cooja.py)
### [api.py](https://github.com/ivanilsonjunior/pythonLogParser/blob/main/api.py)
It's responsible for presenting experiments, their runs and generated data. It was made in Flask, and the user can create new simulations and runs. The generated information is presented by layer.
### [Model.py](https://github.com/ivanilsonjunior/pythonLogParser/blob/main/Model.py)
It's responsible for processing all the things. It's my attempt to develop using the Object-oriented paradigm.
TODO: Split apart the data from the presentation

## Install and Run
1. Inside the [Contiki-NG](https://github.com/contiki-ng/contiki-ng) examples folder clone this repository
    ```
   mkdir deploy
   cd deploy/
   git clone https://github.com/contiki-ng/contiki-ng.git
   cd contiki-ng/
   git submodule update --init --recursive
   cd examples/
   git clone https://github.com/ivanilsonjunior/pythonLogParser.git
   cd pythonLogParser/
   . runMe.sh
   ```
2. Finnaly, just run 'python3 api.py' 
 ## Command-Line
 1. You can use ipython:
   ```
   load Model.py
   exp = Experiment(name = "Test Experiment", experimentFile = "Metrics25m2Node.csc")
   db.add(exp)
   db.commit() # After that you have a saved experiment, and you can run
   exp.runs # List of runs linked to that experiment
   exp.run() # Run the Experiment
   r = exp.runs[0] # Gets the first run
   r = db.query(Run).filter_by(id=1).first() # Returns the id 1 run
   r.records # Shows the run record list
   len(db.query(Record).filter_by(run = r).filter_by(node = 2).filter_by(recordType = "TSCH").all()) # Shows the quantity of TSCH records from node 2
   ```


**Due to my programming skills limitation, I've decided to write the "_FrontEnd_" using Jinja Templates over Flask**
