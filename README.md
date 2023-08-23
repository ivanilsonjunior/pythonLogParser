# Cooja Log Parser

Another Log Parser for Contiki-NG Experiments.
**Based on [examples/benchmarks/result-visualization](https://github.com/contiki-ng/contiki-ng/tree/develop/examples/benchmarks/result-visualization)**, the program uses the same node.c

## What it does:
- Controls the Cooja's Experiments
- Runs Cooja on non-GUI mode
- Keeps the generated data
- Supports bulk run (various run with a new generated random seed)
- Uses the based example node.c as a mote. (node.c create)
- Needs authentication for some tasks (admin:letmein)
- After the run, the log is parsed to an ORM
- Metrics and network behaviour could be extracted from ORM

## Live Demonstration
You can access a live demo: [http://coimbra.ifrn.edu.br/nalpios/](http://coimbra.ifrn.edu.br/nalpios/) or

You can access a [run example](http://coimbra.ifrn.edu.br/nalpios/run/3)

## Classes
### [Runner.py](https://github.com/ivanilsonjunior/pythonLogParser/blob/main/Runner.py)
It's responsible for calling Cooja and running the experiments could easily used for calling the Cooja by other projects. It is an encapsulated version of [run-cooja.py](https://github.com/contiki-ng/contiki-ng/blob/develop/examples/benchmarks/result-visualization/run-cooja.py)
### [api.py](https://github.com/ivanilsonjunior/pythonLogParser/blob/main/api.py)
It's responsible for presenting experiments, their runs and generated data. It was made in Flask, and the user can create new simulations and runs. The generated information is presented by layer.
### [Model.py](https://github.com/ivanilsonjunior/pythonLogParser/blob/main/Model.py)
It's responsible for processing all the things. It's my trying to develop using the Object Oriented paradigm.
TODO: Split apart the data from the presentation

## Install and Run

### Ubuntu 20.04 server and default-jdk (done at 20220729)
1. Inside the [Contiki-NG](https://github.com/contiki-ng/contiki-ng) examples folder clone this repository
   1. The JAVA_HOME variable must be set
2. After the cloning part execute '''python3 -m pip install -r requirements.txt'''
3. Inside the created folder, execute the API 'python3 api.py'.
   - At the first run a SQLite DB Metrics.db will be created
   - You should access the page via browser (http://localhost:9001) and add an experiment (Click on 'Add Experiment' link and put any name, and the Simulation file puts Sim.csc)
   - Inside the experiment page, click on the new Run
   - After the done, you can extract the metrics from the run
 4. I made an installation over a freshly installed Debian 10, and it worked fine.
   ```
   mkdir deploy
   cd deploy/
   git clone https://github.com/contiki-ng/contiki-ng.git
   sudo apt install build-essential doxygen git curl wireshark python3-serial srecord rlwrap default-jre ant openjdk-11-jdk python3-pip
   export JAVA_HOME=/usr/lib/jvm/default-java
   cd contiki-ng/
   git submodule update --init --recursive
   cd examples/
   git clone https://github.com/ivanilsonjunior/pythonLogParser.git
   cd pythonLogParser/
   . runMe.sh
   ``` 
   After, just run 'python3 api.py'
  
### Debian 10 and default-jdk

1. Inside the [Contiki-NG](https://github.com/contiki-ng/contiki-ng) examples folder clone this repository
   1. The JAVA_HOME variable must be set
2. After the cloning part execute '''python3 -m pip install -r requirements.txt'''
3. Inside the created folder, execute the API 'python3 api.py'.
   - At the first run a SQLite DB Metrics.db will be created
   - You should access the page via browser (http://localhost:9001) and add an experiment (Click on the 'Add Experiment' link and put any name, and the Simulation file puts Sim.csc)
   - Inside the experiment page, click on the new Run
   - After the done, you can extract the metrics from the run
 4. I made an installation over a freshly installed Debian 10, and it worked fine.
   ```
   mkdir deploy
   cd deploy/
   git clone https://github.com/contiki-ng/contiki-ng.git
   sudo apt install build-essential doxygen git curl wireshark python3-serial srecord rlwrap default-jre ant openjdk-11-jdk python3-pip
   export JAVA_HOME=/usr/lib/jvm/default-java
   cd contiki-ng/
   git submodule update --init --recursive
   cd examples/
   git clone https://github.com/ivanilsonjunior/pythonLogParser.git
   cd pythonLogParser/
   . runMe.sh
   ```
### CentOS
1. Preamble
   1. Install necessary packages/repos
      ```
      sudo yum groupinstall 'Development Tools' # I know... It's a lazy way... But be free to contribute with a refinement
      sudo yum install ant
      mkdir deploy # Target folder
      cd deploy
      git clone https://github.com/contiki-ng/contiki-ng.git # Contiki-NG Repo
      git submodule update --init --recursive # Submodules (Eg: Cooja)
      ```
   2. Configure the Java Environment (You should put on .bashrc)
      ```
      export JAVA_HOME=$(dirname $(dirname $(readlink $(readlink $(which javac)))))
      export PATH=$PATH:$JAVA_HOME/bin
      export CLASSPATH=.:$JAVA_HOME/jre/lib:$JAVA_HOME/lib:$JAVA_HOME/lib/tools.jar
      ```
2. Inside the [Contiki-NG](https://github.com/contiki-ng/contiki-ng) examples folder clone this repository
   ```
   cd $WHEREVER_YOUR_CONTIKI-NG_FOLDER_IS/examples/
   git clone https://github.com/ivanilsonjunior/pythonLogParser.git
   cd pythonLogParser/
   . runMe.sh
   python3 api.py
   ```
 
 ### Command-Line
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
