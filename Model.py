'''

Model class for Cooja System Log Parser

'''
from datetime import datetime
from hashlib import new
from re import S
import re
import os
import statistics
from types import new_class
from typing import Counter
from xml.dom import minidom
from numpy import apply_along_axis, median
import matplotlib
from sqlalchemy.sql.base import Executable
from sqlalchemy.sql.sqltypes import PickleType
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.mutable import MutableList
matplotlib.use('Agg')
import threading
import itertools
import pandas as pd
#import gc

from sqlalchemy.sql.elements import TextClause
from Runner import Runner
from sqlalchemy import create_engine, MetaData, ForeignKey, Column, Integer, String, Float, DateTime, Boolean, engine
from sqlalchemy.orm import relationship
#Para realizar as alterações/consultas
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, inspect
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
from sqlalchemy.sql.expression import label, null
from sqlalchemy.orm import class_mapper
from sqlalchemy import orm



DBName = "Metrics.db"
fileEngine = create_engine('sqlite:///' + DBName, connect_args={'check_same_thread': False}, echo = False)

DBMemory = ":memory:"
memEngine = create_engine('sqlite:///' + DBMemory, connect_args={'check_same_thread': False}, echo = False)
memConnection = memEngine.raw_connection().connection
engine = fileEngine

meta = MetaData()
meta.bind = engine
Base = declarative_base(metadata=meta)
Session = sessionmaker(bind=engine)
db = Session()

class Experiment(Base):
    '''
    Represents an experiment, an experiment is composed by a .csc scenario file that will be run once or more times.

        Parameters:
            name: Experiment Name
            parameters: Experiment parameters (Could be refactored)
            experimentFile: Cooja .csc simulation
            records: Generated records after run
    '''
    __tablename__ = 'experiments'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    #parameters = Column(String (200), nullable=False)
    experimentFile = Column(String (200), nullable=False)
    confFile_id = Column(Integer, ForeignKey('projectconf.id'))
    confFile = relationship("ProjectConfFile", uselist=False)
    def run(self):
        runner = Runner(str(self.experimentFile))
        newRun = Run()
        newRun.maxNodes = len(minidom.parse(self.experimentFile).getElementsByTagName('id'))+1 #To use the node.id directly untedns
        newRun.experiment = self
        newRun.start = datetime.now()
        try:
            runner.run()
            newRun.end = datetime.now()
            newRun.processRun()
            newRun.parameters = newRun.getParameters()
            self.runs.append(newRun)
            newRun.metric = Metrics(newRun)
            db.add(newRun)
            db.commit()
            newRun.metric.application.process()
            return "Done"
        except Exception as ex:
            print (ex)
            return "Error"

    def bulkRun(self, dictVariations, repetitions):
        '''
        bulkRun was made for perform various run by variation of project.conf parameters. You should pass a dict with project.conf defines variations ex: dictVariations = {'TSCH_SCHEDULE_CONF_DEFAULT_LENGTH': [5,7,9], 'APP_SEND_INTERVAL_SEC': [1,3,5]} and the number of repetitions
        '''
        keys, values = zip(*dictVariations.items())
        permutations_dicts = [dict(zip(keys, v)) for v in itertools.product(*values)]
        for i in permutations_dicts:
            for k in i.keys():
                self.confFile.defines[k] =  i[k]
            # Creating temp folder
            import os
            import shutil
            if os.path.isdir("temp"):
                shutil.rmtree("temp")
            os.mkdir("temp")
            #copying files
            shutil.copy(self.experimentFile, "temp")
            shutil.copy("Makefile","temp")
            # TODO: I Should get the mote.c file via .csc file
            shutil.copy("node-rt.c","temp")
            shutil.copy("sf-simple.c","temp")
            shutil.copy("sf-simple.h","temp")
            self.confFile.save("temp/project-conf.h")
            #Adjsting the Makefile for the Contiki's right place
            with open('temp/Makefile','r') as file:
                filedata = file.read()
                filedata = filedata.replace('../..','../../..')
            with open('temp/Makefile','w') as file:
                file.write(filedata)
            for run in range(repetitions):
                runOk = False
                while(not runOk):
                    print("Run " + str(run) + " of " + str(repetitions) + " values: " + str(i.values()))
                    import lxml.etree
                    import random
                    simFile = lxml.etree.parse(str("temp/" + self.experimentFile))
                    rand = simFile.xpath("//randomseed")[0]
                    rand.text = str(random.randint(0,65535))
                    open(str("temp/" + self.experimentFile), 'w').write(lxml.etree.tounicode(simFile))
                    runner = Runner(str("temp/" + self.experimentFile))
                    newRun = Run()
                    newRun.maxNodes = len(minidom.parse("temp/" + self.experimentFile).getElementsByTagName('id'))+1 #To use the node.id directly untedns
                    newRun.experiment = self
                    newRun.start = datetime.now()
                    retorno = runner.run()
                    if (retorno == -1):
                        continue
                    else:
                        newRun.end = datetime.now()
                        newRun.processRun()
                        newRun.parameters = newRun.getBulkParameters()
                        self.runs.append(newRun)
                        newRun.metric = Metrics(newRun)
                        db.add(newRun)
                        db.commit()
                        newRun.metric.application.process()
                        runOk = True

    def toCsv(self, filename):
        '''
        Its a personal demanding for my experiements. In my experiments I have run with SlotFrame length [5,7 and 11] and APP_SEDD_INTERVAL of [3600(No App data), 1, 2, 3, 4, 5]
        '''
        self = self
        sfLen = ['5','7','11']
        sendInterval = ['1200','1','2','3','4','5']
        dataset = {}
        dados = []        
        for r in self.runs:
            dataset[self.experimentFile] = {}
            for sf in sfLen:
                dataset[str(self.experimentFile)][sf] = {}
                for s in sendInterval:
                    dataset[str(self.experimentFile)][sf][s] = []
        for r in self.runs:
            for sf in sfLen:
                try:
                    if r.parameters['TSCH_SCHEDULE_CONF_DEFAULT_LENGTH'] == sf:
                        #Put Here your metrics
                        print("Run id: "+ str(r.id))
                        dataset[str(self.experimentFile)][r.parameters['TSCH_SCHEDULE_CONF_DEFAULT_LENGTH']][r.parameters['APP_SEND_INTERVAL_SEC']].append(r.metric.getSummary())
                        #gc.collect()
                except Exception:
                    continue
        for e in dataset.keys():
            for sfleng in dataset[e].keys():
                for sentInt in dataset[e][sfleng].keys():
                    df = pd.DataFrame(dataset[e][sfleng][sentInt])
                    data = {}
                    data['SlotFrame Length'] = sfleng
                    data['Sent Interval'] = sentInt
                    data.update(json.loads(df.mean().to_json()))
                    dados.append(data)
                    del data
        df = pd.json_normalize(dados) 
        df.to_csv(filename)
        dados = []
        for e in dataset.keys():
            for sfleng in dataset[e].keys():
                for sentInt in dataset[e][sfleng].keys():
                    df = pd.DataFrame(dataset[e][sfleng][sentInt])
                    data = {}
                    data['SlotFrame Length'] = sfleng
                    data['Sent Interval'] = sentInt
                    data.update(json.loads(df.std().to_json()))
                    dados.append(data)
        df = pd.json_normalize(dados)         
        df.to_csv("STD"+filename)        

class Run(Base):
    '''
    Represents a run experiment, a experiment file can me customisated by the Makefile and project.conf files, those customisations should be registed by the parameters dict property. The scenario is run, and after that, the generated log is parsed to a Record object linked on Run (One to Many)

        Parameters:
            start: Start simulation time
            end: End simulation time
            parameters: Run parameters
            experiment: Experiment base
            metric: Metrics simulation
    '''
    __tablename__ = "runs"
    id = Column(Integer,primary_key=True)
    start = Column(DateTime)
    end = Column(DateTime)
    maxNodes = Column(Integer)
    parameters = Column(PickleType)
    experiment_id = Column(Integer, ForeignKey('experiments.id')) # The ForeignKey must be the physical ID, not the Object.id
    experiment = relationship("Experiment", back_populates="runs")
    metric = relationship("Metrics", uselist=False, back_populates="run")

    def __str__(self) -> str:
        layer = {}
        try:
            layer['mac'] = self.parameters['MAKE_MAC'].split('_')[-1]
        except:
            layer['mac'] = "TSCH"
        try:
            layer['rpl'] = self.parameters['MAKE_ROUTING'].split('_')[-1]
        except:
            layer['rpl'] = "LITE"
        try:
            layer['net'] = self.parameters['MAKE_NET'].split('_')[-1]
        except:
            layer['net'] = "IPV6"
            
        return "ID: {} Exp: {} MAC: {mac} ROUTING: {rpl} NET: {net}".format(self.id ,self.experiment.id, **layer)


    def printNodesPosition(self):
        from mpl_toolkits.mplot3d import Axes3D
        import matplotlib.pyplot as plt
        import io
        import base64
        tempBuffer = io.BytesIO()
        plt.clf()
        nodes = []
        x = []
        y = []
        z = []
        for node, position in self.getNodesPosition().items():
            nodes.append(node)
            x.append(position['x'])
            y.append(position['y'])
            z.append(0)
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(x, y, z, c='b', marker='o')
        i = 0
        for label in nodes:
            ax.text(x[i],y[i],z[i], label)
            i += 1

        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        #ax.set_zlabel('Z Label')
        ax.set_title("Nodes position")
        ax.set_zlim3d(0,100)

        plt.savefig(tempBuffer, format = 'png')
        return base64.b64encode(tempBuffer.getvalue()).decode()

    def getNodesPosition(self):
        myData = {}
        for i in range(2,(self.maxNodes)):
            myData['N' + str(i)] = {}
        doc = minidom.parse(self.experiment.experimentFile)
        for i in doc.getElementsByTagName('mote'):
            try:
                myId = str(i.getElementsByTagName('id')[0].firstChild.data)
                x = float(i.getElementsByTagName('x')[0].firstChild.data)
                y = float(i.getElementsByTagName('y')[0].firstChild.data)
                myData['N' + myId] = {'x' : x, 'y' : y}
            except:
                None
        return myData


    def processRun(self):
        with open("COOJA.testlog", "r") as f:
            for line in f.readlines():
                if (line.startswith("Random") or line.startswith("Starting") or line.startswith("Script timed out") or line.startswith("TEST OK")):
                    continue
                if (line.startswith("Test ended at simulation time:")):
                    simTime = int(line.split(":")[1].strip())
                    continue
                fields = line.split()
                logTime = fields[0]
                if (fields[2].startswith("Assertion")):
                    continue
                logNode = int(fields[1])
                try:
                    logDesc = re.findall("\[(.*?)\]", line)[0].split(":")
                except Exception:
                    continue
                logLevel = logDesc[0].strip()
                logType = logDesc[1].strip()
                data = line.split("]")[1].strip()
                newRecord = Record(logTime,logNode,logLevel,logType,data,self)
                #db.add(newRecord)
                self.records.append(newRecord)
    
    def getParameters(self):
        '''
        Adapted from: https://stackoverflow.com/questions/2804543/read-subprocess-stdout-line-by-line
        '''
        import subprocess
        proc = subprocess.Popen(['make','viewconf'],bufsize=1, universal_newlines=True, stdout=subprocess.PIPE)
        myDict = {}
        # Get last line source: https://stackoverflow.com/questions/46258499/how-to-read-the-last-line-of-a-file-in-python
        with open('COOJA.testlog', 'rb') as f:
            try:  # catch OSError in case of a one line file 
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
            except OSError:
                f.seek(0)
            last_line = f.readline().decode()
            myDict['SimTimeout'] = int(last_line.split(':')[1])/1000000
        for param in ['radiomedium','transmitting_range','interference_range','success_ratio_tx','success_ratio_rx']:
            myDict[param] = str(minidom.parse(self.experiment.experimentFile).getElementsByTagName(param)[0].firstChild.data).strip()
        for line in iter(proc.stdout.readline,''):
            if not line:
                break
            if line.startswith("####"):
                line = line.split()
                try:
                    #print (line[1].split("\"")[1] , "value", line [4])
                    myDict[line[1].split("\"")[1]] = line [4]
                except IndexError:
                    if (line[1].split("\"")[1].startswith("MAKE")):
                        #print (line[1].split("\"")[1] , "value", line [3])
                        myDict[line[1].split("\"")[1]] = line [3]
                        continue
                    continue
        return myDict

    def getBulkParameters(self):
        '''
        Adapted from: https://stackoverflow.com/questions/2804543/read-subprocess-stdout-line-by-line
        '''
        import subprocess
        proc = subprocess.Popen(['make','viewconf'],bufsize=1, cwd="temp", universal_newlines=True, stdout=subprocess.PIPE)
        myDict = {}
        # Get last line source: https://stackoverflow.com/questions/46258499/how-to-read-the-last-line-of-a-file-in-python
        with open('COOJA.testlog', 'rb') as f:
            try:  # catch OSError in case of a one line file 
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
            except OSError:
                f.seek(0)
            last_line = f.readline().decode()
            myDict['SimTimeout'] = int(last_line.split(':')[1])/1000000
        for param in ['randomseed','radiomedium','transmitting_range','interference_range','success_ratio_tx','success_ratio_rx']:
            myDict[param] = str(minidom.parse(self.experiment.experimentFile).getElementsByTagName(param)[0].firstChild.data).strip()
        for line in iter(proc.stdout.readline,''):
            if not line:
                break
            if line.startswith("####"):
                line = line.split()
                try:
                    #print (line[1].split("\"")[1] , "value", line [4])
                    myDict[line[1].split("\"")[1]] = line [4]
                except IndexError:
                    if (line[1].split("\"")[1].startswith("MAKE")):
                        #print (line[1].split("\"")[1] , "value", line [3])
                        myDict[line[1].split("\"")[1]] = line [3]
                        continue
                    continue
        return myDict

    def getRunDuration(self) -> DateTime:
        '''
            Return the run duration time.
        '''
        return self.end - self.start

class ProjectConfFile(Base):
    '''
    Represents the project-conf.h file
    '''
    __tablename__ = 'projectconf'
    id = Column(Integer, primary_key=True)
    defines = Column(MutableDict.as_mutable(PickleType))

    def __init__(self):
        defines = {}
    
    def getFileContents(self):
        content = ""
        for k, v in self.defines.items():
            content += ("#define " + k + " " + str(v) + "\n")
        return content
    
    def save(self, filename):
        with open(filename, "w") as file:
            file.write(self.getFileContents())

class Record(Base):
    '''
    Represents an experiment's record
        Parameters:
            simTime: Simulation time of record (Microseconds 10^ -6)
            node: Number of the node that generates the record
            recordLevel: Level of record (Info, Warn, Debug)
            recordType: Type (App, Protocol, Layer, etc)
            rawData: Record string
            run: Run that owns this record

    '''
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True)
    simTime = Column(Integer, nullable=False)
    node = Column(Integer, nullable=False)
    recordLevel = Column(String(50), nullable=False)
    recordType = Column(String(50), nullable=False)
    rawData = Column(String(200), nullable=False)
    run_id = Column(Integer, ForeignKey('runs.id')) # The ForeignKey must be the physical ID, not the Object.id
    run = relationship("Run", back_populates="records")
    def __init__(self,simtime, node,level,type,data,run):
        self.simTime = simtime
        self.node = node
        self.recordLevel = level
        self.recordType = type
        self.rawData = data
        self.run = run

class Node(Base):
    '''
    TODO: Represents a note (Position and Metrics)
    '''
    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True)
    simId = Column(Integer, primary_key=True)
    posX = Column(Integer, nullable=False)
    posY = Column(Integer, nullable=False)
    posZ = Column(Integer, nullable=False)

class Metrics(Base):
    '''
    This is the metrics container. TODO: Assemble
    '''
    __tablename__ = 'metrics'
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey('runs.id')) # The ForeignKey must be the physical ID, not the Object.id
    run = relationship("Run", back_populates="metric")
    #application_id = Column(Integer, ForeignKey('application.id')) # The ForeignKey must be the physical ID, not the Object.id
    application = relationship("Application", uselist=False, back_populates="metric")
    mac_id = Column(Integer, ForeignKey('mac.id')) # The ForeignKey must be the physical ID, not the Object.id
    mac = relationship("MAC", back_populates="metric")
    rpl_id = Column(Integer, ForeignKey('rpl.id')) # The ForeignKey must be the physical ID, not the Object.id
    rpl = relationship("RPL", back_populates="metric")
    energy_id = Column(Integer, ForeignKey('energy.id')) # The ForeignKey must be the physical ID, not the Object.id
    energy = relationship("Energy", back_populates="metric")
    linkstats_id = Column(Integer, ForeignKey('linkstats.id')) # The ForeignKey must be the physical ID, not the Object.id
    linkstats = relationship("LinkStats", back_populates="metric")


    def __init__(self, run):
        self.run = run
        #print("Self lenght:" , len(self.run.records) )
        self.application = Application(self)
        #self.application.process()
        #print("Processing MAC")
        if run.parameters['MAKE_MAC'] ==  "MAKE_MAC_TSCH":
            self.mac = MAC(self)
        #print("Processing LinkStatus")
        self.linkstats = LinkStats(self)
        #print("Processing RPL")
        self.rpl = RPL(self)
        #print("Processing Energy")
        self.energy = Energy(self)

    def getSummary(self):
        '''
        Here you should return the metrics that you want
        '''
        retorno = {}
        print ("App", end =" ")
        retorno['app-latency'] = self.application.latency.latencyMean()
        retorno['app-latency-median'] = self.application.latency.latencyMedian()
        retorno['app-pdr'] = self.application.pdr.getGlobalPDR()
        retorno['app-genPkg'] = len(self.application.records)
        print ("RPL", end =" ")
        retorno['rpl-parentsw'] = self.rpl.getParentSwitches()
        #retorno['rpl-avgHops'] = self.rpl.getAverangeHops(slice=600000000)
        #retorno['rpl-avgHopsSliced'] = self.rpl.getAverangeHops()
        rplMessages = ['total','multicast-DIO','unicast-DIO','DIS','DAO','DAO-ACK']
        rplType = self.rpl.getControlMessages()
        for typ in rplMessages:
            chave = str('rpl-msg-'+ typ)
            retorno.setdefault(chave,0)
            try:
                retorno[chave] = rplType[typ]
            except KeyError:
                retorno[chave] = 0
        print ("MAC", end =" ")
        print("Retransmissions", end =" ")
        retransmissions = self.mac.getRetransmissions()
        retorno['mac-retransmissions'] = retransmissions['retransmissions']
        retorno['mac-retransRate'] = retransmissions['retransRate']
        print("Disconnections", end =" ")
        retorno['mac-disconnections'] = self.mac.getDisconnections()
        retorno['mac-formation'] = 0#self.mac.formationTime()
        #nbrQueue = self.mac.getNBRQueueOccupation()
        #retorno['mac-queuenbr-length'] = nbrQueue['length']
        #retorno['mac-queuenbr-occupation'] = nbrQueue['occupation']
        #retorno['mac-queuenbr-variance'] = nbrQueue['variance']
        #globalQueue = self.mac.getGlobalQueueOccupation()
        #retorno['mac-queueglobal-length'] = globalQueue['length']
        #retorno['mac-queueglobal-occupation'] = globalQueue['occupation']
        #retorno['mac-queueglobal-variance'] = globalQueue['variance']
        print("PDR", end =" ")
        retorno['link-pdr'] = self.linkstats.getPDR()['PDR']
        print ("Energy RDC", end =" ")
        retorno['energy-RDC'] = self.energy.getRadioDutyCicle()
        print ("Energy Channel", end =" ")
        retorno['energy-ChannelOccupation'] = self.energy.getChannelUtilization()
        print("END")
        return retorno

class Application(Base):
    __tablename__ = 'application'
    id = Column(Integer, primary_key=True)
    metric_id = Column(Integer, ForeignKey('metrics.id')) # The ForeignKey must be the physical ID, not the Object.id
    metric = relationship("Metrics", back_populates="application")
    latency_id = Column(Integer, ForeignKey('latencies.id')) # The ForeignKey must be the physical ID, not the Object.id
    latency = relationship("Latency", back_populates="application")
    pdr_id = Column(Integer, ForeignKey('pdrs.id')) # The ForeignKey must be the physical ID, not the Object.id
    pdr = relationship("PDR", back_populates="application")
    records = relationship("AppRecord", back_populates="application")


    def __init__(self,metric):
        self.metric = metric
        self.latency = Latency(self)
        self.pdr = PDR(self)

    def process(self):
        print("Processing App")
        data = self.metric.run.records
        for rec in data:
            if rec.rawData.startswith("app generate"):
                sequence = int(rec.rawData.split()[3].split("=")[1])
                node = int(rec.rawData.split()[4].split("=")[1])
                genTime = int(rec.simTime)
                dstNode = 1 #That simulation doesn't define a customized sink
                #print("Node: " ,  node , "Seq: " , sequence , "Generation Time: ", genTime ,"Destination" , dstNode)
                newLatRec = AppRecord(genTime,node,dstNode,sequence)
                newLatRec.rcv = False
                db.add(newLatRec)
                self.records.append(newLatRec)
                continue
            
            if rec.rawData.startswith("app receive"):
                sequence = int(rec.rawData.split()[3].split("=")[1])
                recTime = int(rec.simTime)
                srcNode = int(rec.rawData.split()[4].split("=")[1].split(":")[5], 16) # Converts Hex to Dec
                for record in self.records:
                    if (record.srcNode == srcNode and record.sqnNumb == sequence):
                        record.rcvPkg(recTime)
                        record.rcv = True
                #print("Node: " ,  srcNode  , "Seq: " , sequence , "Receive Time: ", recTime)
                        break
        db.commit()
        print("Done")

class RPL(Base):
    '''
    RPL Metrics Class
    '''
    __tablename__ = 'rpl'
    id = Column(Integer, primary_key=True)
    metric = relationship("Metrics", uselist=False, back_populates="rpl")

    def __init__(self,metric):
        self.metric = metric
    
    def processParentSwitches(self) -> dict:
        results = {}
        for i in range(1,(self.metric.run.maxNodes)):
            results[str(i)] = []
        data = [rec for rec in self.metric.run.records if rec.recordType == "RPL" and "parent switch:" in rec.rawData]
        reExp = re.compile('\((.*?)\)')
        for sw in data:
            old = ':'.join(map(str, sw.rawData.split('->')[0].split(":")[1:])).strip()
            new = sw.rawData.split('->')[1].strip()
            if reExp.search(old): 
                old = None
            if reExp.search(new):
                new = None            
            results[str(sw.node)].append({'time' : sw.simTime, 'old' : old, 'new' : new})
        del data
        return results

    def getParentSwitches(self) -> int:
        retorno = 0
        psw = self.processParentSwitches()
        for i in psw:
            retorno += len(psw[i])
        return retorno

    def getControlMessages(self) -> dict:
        '''
        Return the total amount of RPL messages and the sum of each message type
        '''
        records = [rec for rec in self.metric.run.records if rec.recordType == "RPL" and "sending a " in rec.rawData]
        retorno = {'total':len(records)}
        for r in records:
            msgType = r.rawData.split(' ')[2]
            retorno.setdefault(msgType, 0)
            retorno[msgType] += 1
        del records
        return retorno

    def getAverangeHops(self, slice = 300000000) -> float:
        '''
        Return the averange RPL hops at end method extracted and adapted from: https://github.com/contiki-ng/contiki-ng/blob/develop/examples/benchmarks/rpl-req-resp/parse.py

        parameters: slice - The time interval for each measured slice
        '''
        isItIpv6 = '((?:(?:[0-9A-Fa-f]{1,4}:){6}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|::(?:[0-9A-Fa-f]{1,4}:){5}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){4}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){3}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,2}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){2}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,4}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}|(?:(?:[0-9A-Fa-f]{1,4}:){,6}[0-9A-Fa-f]{1,4})?::))'
        parents = {}
        time = slice
        anterior = 0
        endtime = self.metric.run.parameters['SimTimeout'] + 1
        retorno = []
        while time < endtime:
            records = [rec for rec in self.metric.run.records if rec.recordType == "RPL" and "links" in rec.rawData and rec.simTime > anterior and rec.simTime < time]
            anterior = time
            time += slice
            for rec in records:
                if rec.recordType == "RPL" and rec.rawData.startswith("links: "):
                    res = re.findall(isItIpv6,rec.rawData)
                    if len(res) == 2:
                        child = int(res[0].split(":")[-1],16)
                        parent = int(res[1].split(":")[-1],16)
                        if not child in parents:
                            parents[child] = {}
                        if not parent in parents:
                            parents[parent] = None
                        parents[child] = parent
            data = []
            for node in range(2,(self.metric.run.maxNodes)): #Starting from 2nd node
                hops = 0
                try: 
                    while(parents[node] != None):
                        node = parents[node]
                        hops += 1
                        if hops > 50:
                            continue
                    data.append(hops)
                except:
                    continue
            try:
                retorno.append(statistics.mean(data))
            except statistics.StatisticsError:
                retorno.append(0)
            del data
            del records
        return statistics.mean(retorno)

    def getMetrics(self):
        '''
        Returns the RPL metrics (Trickle Timer and Rank)
        '''
        retorno = []
        data = [rec for rec in self.metric.run.records if rec.recordType == "RPL"]
        for rec in data:
            res = re.compile('.*?state: (\w*),.*? rank (\d*).*?dioint (\d*).*?nbr count (\d*)').match(rec.rawData)
            if (res):
                rank = int(res.group(2))
                trickle = (2**int(res.group(3)))/(60*1000.)
                nbrCount = int(res.group(4))
                retorno.append({'node': rec.node, 'rank': rank, 'trickle': trickle, "state":res.group(1)})
        return retorno

    def printMetrics(self):
        '''
        Returns the boxplot of the metrics data
        '''
        import io
        import base64
        import matplotlib.pyplot as plt
        c = 0
        fig, axes = plt.subplots(figsize=(10,5),ncols=2)
        df = pd.DataFrame(self.getMetrics())
        fig.tight_layout(pad=1.5)

        for i in ['trickle','rank']:
        #dfg = df.groupby('state').sum().plot(kind='box')
        #df.describe()
        #ax = plt.subplot(4, 2)
            ax = df[i].plot(kind='box', rot = 90, fontsize= '8', grid = True, title=self.metric.run.experiment.name + " - " + i, ax=axes[c])
            ax.set_ylim(ymin=0)
            if i == 'trickle':
                ax.set_ylabel("Seconds")
            c += 1
        tempBuffer = io.BytesIO()
        plt.savefig(tempBuffer, format = 'png')
        return base64.b64encode(tempBuffer.getvalue()).decode()

    def printParentSwitches(self):
        data = {}
        results = self.processParentSwitches()
        from collections import Counter
        index = 2
        import io
        import base64
        import matplotlib.pyplot as plt
        plt.clf()
        for k in results:
            if k == "0" or k == "1":
                continue
            swCount = len(results[k])
            data[index] = swCount
            index += 1
            width = 0.8
            #plt.text(((index-1) - (width/3)), swCount-2, str(swCount), color="black", fontsize=8)
        tempBuffer = io.BytesIO()
        plt.bar(data.keys(),data.values(), width=width, label="Parent Switches")
        #plt.bar_label(data.values(), padding=2)
        plt.xticks(list(data.keys()))
        #plt.ylim([0, 100])
        plt.xlabel("Nodes")
        plt.ylabel("Parent Switches")
        #plt.legend()
        plt.gcf().set_size_inches(8,6)
        plt.savefig(tempBuffer, format = 'png')
        return base64.b64encode(tempBuffer.getvalue()).decode()
    

    '''
        First attemp to get a network overview at simulation's end
    '''
    def printNetwork(self):
        import networkx as nx
        import matplotlib.pyplot as plt
        import io
        import base64
        import math
        tempBuffer = io.BytesIO()
        plt.clf()
        G = nx.DiGraph()
        npos = self.metric.run.getNodesPosition()
        gpos = {}
        for node in npos:
            gpos [node] =  (npos[node]['x'],npos[node]['y'])
        data = self.processParentSwitches()
        for i in data:
            if i == '0' and i == '1':
                continue
            if i == '1':
                G.add_node(str('N'+i))
                continue
            nodeOrigin = str('N' + i)
            try:
                nodeParent = data[i].pop()['new'] # Get the last change
            except IndexError:
                continue
            if nodeParent == None:
                G.add_node(nodeOrigin)
                continue
            else:
                G.add_edge(nodeOrigin,str('N'+ str(int(nodeParent.split(":")[-1], 16))))
        val_map = {'N1': 1.0}
        fig, ax = plt.subplots()
        ylm = {'min': min(npos.values(), key=lambda y:y['y'])['y'], 'max': max(npos.values(), key=lambda y:y['y'])['y']}
        ylimit = range(math.floor(ylm['min']),math.ceil(ylm['max'])+1)
        plt.yticks(ylimit)
        plt.yscale("linear")
        plt.xlabel("X Position (m)")
        plt.ylabel("Y Position (m)")
        nx.draw_networkx_nodes(G, pos=gpos, ax=ax)
        nx.draw_networkx_labels(G, pos=gpos, ax=ax)
        nx.draw_networkx_edges(G, pos=gpos, ax=ax)
        ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
        ax.set_title("Nodes Parent")
        plt.gcf().set_size_inches(8,6)
        #plt.show()
        #
        plt.savefig(tempBuffer, format = 'png')
        return base64.b64encode(tempBuffer.getvalue()).decode()

class MACMessage(Base):
    '''
    Represents a regular MAC message
    '''
    __tablename__ = 'macmessage'
    id = Column(Integer, primary_key=True)
    origin = 0
    dest = 0
    enQueued = 0
    seqno = 0
    queueNBROccupied = 0
    queueNBRSize = 0
    queueGlobalOccupied = 0
    queueGlobalSize = 0
    headerLen = 0
    dataLen = 0
    sentTime = 0
    status = 0
    tries = 0
    rcvTime = 0
    isReceived = False
    isSent = False
    def __init__(self,origin,dest,enQue,seqno,queueNBROccupied,queueNBRSize,queueGlobalOccupied,queueGlobalSize,headerLen,dataLen):
        self.origin = origin
        self.dest = dest
        self.enQueued = enQue
        self.seqno = seqno
        self.queueNBROccupied = queueNBROccupied
        self.queueNBRSize = queueNBRSize
        self.queueGlobalOccupied = queueGlobalOccupied
        self.queueGlobalSize = queueGlobalSize
        self.headerLen = headerLen
        self.dataLen = dataLen
    def sent(self, time, status, tx):
        self.sentTime = time
        self.status = status
        self.tries = tx
        self.isSent = True
    def receive(self, time):
        self.rcvTime = time
        self.isReceived = True
    def latency(self):
        if not self.isSent:
            raise Exception("Message didn't send")
        if not self.isReceived:
            raise Exception("Message not received")
        return self.rcvTime - self.enQueued
    def retransmissions(self):
        if not self.isSent:
            raise Exception("Message didn't send")
        if not self.isReceived:
            raise Exception("Message not received")
        return self.tries - 1
    def transmissions(self):
        if not self.isSent:
            raise Exception("Message didn't send")
        if not self.isReceived:
            raise Exception("Message not received")
        return self.tries
    def __str__(self) -> str:
        return "{self.origin}<->{self.dest} Q:{self.enQueued} S({self.isSent}):{self.sentTime} S({self.isReceived}):{self.rcvTime} Sq:{self.seqno}".format(self=self)

class MAC(Base):
    '''
    Represents the MAC Layer
    TODO: In future a factory method should return the self.metric.run.parameters['MAKE_MAC'] instance, now is implemented by an ungainly if/else statement
    '''
    __tablename__ = 'mac'
    id = Column(Integer, primary_key=True)
    metric = relationship("Metrics", uselist=False, back_populates="mac")
    results = Column(PickleType)

    def __init__(self,metric):
        self.metric = metric
        self.processFrames()

    #@orm.reconstructor
    def processFrames(self):
        results = {}
        for i in range(0,(self.metric.run.maxNodes)):
            results[str(i)] = []
        results['65535'] = []

        if self.metric.run.parameters['MAKE_MAC'].split('_')[-1] == "TSCH":
            data = [rec for rec in self.metric.run.records if rec.recordType == "TSCH"]
            for rec in data:
                if rec.rawData.startswith("send packet to"):
                    origin = int(rec.node)
                    dest = int(rec.rawData.split()[3].split('.')[0], 16)
                    enQueued = float(rec.simTime)
                    seqnum = int(rec.rawData.split()[6].replace(',',''))
                    queueNBROccupied = int(rec.rawData.split()[8].split('/')[0])
                    queueNBRSize = int(rec.rawData.split()[8].split('/')[1])
                    queueGlobalOccupied = int(rec.rawData.split()[9].replace(',','').split('/')[0])
                    queueGlobalSize = int(rec.rawData.split()[9].replace(',','').split('/')[1])
                    headerLen = int(rec.rawData.split()[11])
                    dataLen = int(rec.rawData.split()[12])
                    macMsg = MACMessage(origin, dest, enQueued, seqnum, queueNBROccupied, queueNBRSize, queueGlobalOccupied, queueGlobalSize, headerLen, dataLen)
                    if macMsg.dest == 0 or macMsg.dest == 65535:
                        macMsg.isReceived = True
                        macMsg.isSent = True
                        macMsg.tries = 1
                    results[str(origin)].append(macMsg)
                    continue
                if rec.rawData.startswith("packet sent to"):
                    dest = int(rec.rawData.split()[3].split('.')[0], 16)
                    seqnum = int(rec.rawData.split()[5].replace(',',''))
                    sentTime = float(rec.simTime)
                    status = int(rec.rawData.split()[7].replace(',',''))
                    tx = int(rec.rawData.split()[9].replace(',',''))
                    for msg in reversed(results[str(rec.node)]):
                        if msg.isSent:
                            continue
                        if ( msg.seqno == seqnum): #and msg.dest == dest):
                            time = sentTime - msg.enQueued 
                            if (time > 10000000):
                                continue
                            else:
                                msg.sent(sentTime, status, tx)
                                if macMsg.dest == 0 or macMsg.dest == 65535:
                                    #Broadcast message is sent by all, I cant control who receives."
                                    # TODO: Figure out why the seqno changes
                                    msg.receive(sentTime)
                                    msg.tries = 1
                                continue
            for rec in data:
                if rec.rawData.startswith("received from"): 
                    dest = int(rec.node)
                    origin = int(rec.rawData.split()[2].split('.')[0], 16)
                    seqnum = int(rec.rawData.split()[5])
                    rcvTime = float(rec.simTime)
                    for msg in results[str(origin)]:
                        if msg.isReceived:
                            continue
                        if msg.seqno == seqnum and msg.dest == dest and msg.isSent and not msg.isReceived:
                            time = rcvTime - msg.sentTime
                            if time < 10000000:
                                msg.receive(rcvTime)
                                break
                            else:
                                None
        else:
            data = [rec for rec in self.metric.run.records if rec.recordType == "CSMA"]
        del data
        self.results =  results
        
    def processIngress(self):
        data = db.query(Record).filter_by(run = self.metric.run).filter_by(recordType = "TSCH").filter(Record.rawData.contains("leaving the network") | Record.rawData.contains("association done")).all()
        #data = [rec for rec in self.metric.run.records if rec.recordType == "TSCH"]
        results = [[] for x in range(self.metric.run.maxNodes)]
        for rec in data:
            if rec.rawData.startswith("leaving the network"):
                results[int(rec.node)].append(tuple((float(rec.simTime)//1000,False)))
                continue
            if rec.rawData.startswith("association done"):
                results[int(rec.node)].append(tuple((float(rec.simTime)//1000, True)))
                continue
        del data
        return results

    def formationTime(self) -> float():
        '''
        Returns the network formation time (ms)
        In case of never had connected, raises an Exception
        '''
        data = [rec for rec in self.metric.run.records if rec.recordType == "TSCH"]
        simNodes = self.metric.run.maxNodes - 1
        connected = 1
        for rec in data:
            if rec.rawData.startswith("leaving the network"):
                connected -= 1
                continue
            if rec.rawData.startswith("association done"):
                connected += 1
                if simNodes == connected:
                    return float(rec.simTime)//1000
        return null
        raise Exception("All Nodes have Never Simultaneously Connected")

    
    def printIngress(self):
        import matplotlib.pyplot as plt
        import io
        import base64
        tempBuffer = io.BytesIO()
        plt.clf()
        index = 2
        results = self.processIngress()
        for i in results[2:]:
            started = 0
            x = [0,0]
            for j in i:
                if j[1]:
                    time = j[0]/1000
                    plt.plot(time, index, marker="^", color="green")
                    x[0] = time
                    x[1] = self.metric.run.parameters['SimTimeout'] #sim end without node's disconnection
                else:
                    time = j[0]/1000
                    plt.plot(time, index, marker="v", color="red")
                    x[1] = time
                    plt.plot(x,[index,index])
                    x = [0,0]
            plt.plot(x,[index,index])
            index +=1
        plt.axvline(x=int(self.metric.run.parameters['APP_WARM_UP_PERIOD_SEC']), label="Warm-up Time", ls=':', c='Orange')
        plt.xlabel("Simulation Time (S)")
        plt.ylabel("Nodes")
        plt.yticks(range(2,self.metric.run.maxNodes))
        plt.title("Node Ingress (TSCH)")
        plt.savefig(tempBuffer, format = 'png')
        return base64.b64encode(tempBuffer.getvalue()).decode()

    def getRetransmissions(self) -> dict():
        '''
        Returns the Experience retransmission metrics

        :returns: dict()
        '''
        retorno = {}
        trams = []
        frames = self.results.items()
        for i, j in frames:
            for m in j:
                if m.isReceived and m.isSent:
                    trams.append(m.retransmissions())
        totalRetrans = sum(trams)
        totalAckFrames = len(trams)
        totalSuccessFrames = Counter(trams)[0] #Success = No need retrams
        retorno['retransmissions'] = totalRetrans
        retorno['totalAck'] = totalAckFrames
        retorno['totalSuccessFrames'] = totalSuccessFrames
        retorno['resFrames'] = totalAckFrames - totalSuccessFrames
        try:
            retorno['retransRate'] = retorno['resFrames']/totalRetrans
        except:
            retorno['retransRate'] = 1
        return retorno

    def printRetransmissions(self):
        import io
        import base64
        import matplotlib.pyplot as plt
        plt.clf()
        tempBuffer = io.BytesIO()
        for i,j in self.results.items():
            # TODO: Process Broadcast messagens
            if i == '0' or i == '65535':
                continue
        #     print (i)
            x = []
            y = []
            for m in j:
                if m.isReceived and m.isSent:
                    x.append(m.sentTime/1000000)
                    y.append(m.retransmissions())
            plt.plot(x, y,linestyle="",marker=".", label = "Node "+str(i))
        plt.axvline(x=int(self.metric.run.parameters['APP_WARM_UP_PERIOD_SEC']), label="Warm-up Time", ls=':', c='Orange')
        plt.xlabel("Simulation Time (s)")
        plt.ylabel("# of Retransmissions")
        plt.legend()
        plt.title("Retransmissions")
        plt.gcf().set_size_inches(8,6)
        plt.savefig(tempBuffer, format = 'png')
        return base64.b64encode(tempBuffer.getvalue()).decode()
    
    def printTransmissions(self):
        import io
        import base64
        import matplotlib.pyplot as plt
        plt.clf()
        tempBuffer = io.BytesIO()
        for i,j in self.results.items():
            # TODO: Process Broadcast messagens
            if i == '0' or i == '65535':
                continue
        #     print (i)
            x = []
            y = []
            for m in j:
                if m.isReceived and m.isSent:
                    x.append(m.sentTime/1000000)
                    y.append(m.retransmissions())
            plt.plot(x, y,linestyle="",marker=".", label = "Node "+str(i))
        plt.axvline(x=int(self.metric.run.parameters['APP_WARM_UP_PERIOD_SEC']), label="Warm-up Time", ls=':', c='Orange')
        plt.xlabel("Simulation Time (s)")
        plt.ylabel("# of Retransmissions")
        plt.legend()
        plt.gcf().set_size_inches(8,6)
        plt.savefig(tempBuffer, format = 'png')
        return base64.b64encode(tempBuffer.getvalue()).decode()

    def getDisconnections(self):
        '''
        Get the amount of disconnections from TSCH
        '''
        itens = []
        for i in self.processIngress():
            for item in i:
                itens.append(item[1])
        return (Counter(itens)[False])

    def getNBRQueueOccupationByNode(self):
        '''
        Returns the NBR queue occupation and the variance by each node
        '''
        import statistics
        retorno = {}
        for i in self.results.keys():
            dataset = []
            if(len(self.results[i]) == 0):
                continue
            queueSize = 64
            for j in self.results[i]:
                dataset.append(j.queueNBROccupied)
            retorno[str('N'+i)] = {'length': statistics.mean(dataset), 'occupation': (statistics.mean(dataset)/queueSize)*100,'variance':statistics.variance(dataset)}
        return retorno

    def getNBRQueueOccupation(self):
        '''
        Returns the NBR queue mean (lenght, occupation%) and the variance
        '''
        import statistics
        retorno = {}
        dataset = []
        frames = 0
        queueOccup = 0
        queueSize = 64
        for i in self.results.keys():
            if(len(self.results[i]) == 0):
                continue
            for j in self.results[i]:
                dataset.append(j.queueNBROccupied)
        retorno =  {'length': statistics.mean(dataset), 'occupation': (statistics.mean(dataset)/queueSize)*100,'variance':statistics.variance(dataset)}
        return retorno

    def getGlobalQueueOccupation(self):
        '''
        Returns the global queue occupation and the variance
        '''
        import statistics
        retorno = {}
        dataset = []
        queueSize = 64
        for i in self.results.keys():
            if(len(self.results[i]) == 0):
                continue
            for j in self.results[i]:
                dataset.append(j.queueGlobalOccupied)
        retorno =  {'length': statistics.mean(dataset), 'occupation': (statistics.mean(dataset)/queueSize)*100,'variance':statistics.variance(dataset)}
        return retorno

    def getGlobalQueueOccupationByNode(self):
        '''
        Returns the global queue occupation and the variance by each node
        '''
        import statistics
        retorno = {}
        for i in self.results.keys():
            dataset = []
            if(len(self.results[i]) == 0):
                continue
            queueSize = 64
            for j in self.results[i]:
                dataset.append(j.queueGlobalOccupied)
            retorno[str('N'+i)] = {'length': statistics.mean(dataset), 'occupation': (statistics.mean(dataset)/queueSize)*100,'variance':statistics.variance(dataset)}
        return retorno

class LinkStats(Base):
    '''
    Link Status

    Class to handle the Link Status level Log
    '''
    __tablename__ = 'linkstats'
    id = Column(Integer, primary_key=True)
    metric = relationship("Metrics", uselist=False, back_populates="linkstats")

    
    def __init__(self,metric):
        self.metric = metric

    def getNodesPDR(self) -> dict:
        nodesStats = {}
        for n in range(self.metric.run.maxNodes):
            nodesStats[n] = {"tx": 0, "ack":0}
        #data = [rec for rec in self.metric.run.records if rec.recordType == "Link Stats"]
        data = db.query(Record).filter_by(run = self.metric.run).filter_by(recordType = "Link Stats").all()
        for rec in data:
            tx = int(rec.rawData.split()[2].split("=")[1])
            ack = int(rec.rawData.split()[3].split("=")[1])
            nodesStats[rec.node]['tx'] = nodesStats[rec.node]['tx'] + tx
            nodesStats[rec.node]['ack'] = nodesStats[rec.node]['ack'] + ack
        return nodesStats

    def getPDR(self):
        nodesStats = self.getNodesPDR()
        total = 0
        totalAck = 0
        for n in range(self.metric.run.maxNodes):
            total = total + nodesStats[n]['tx']
            totalAck = totalAck + nodesStats[n]['ack']
        try:
            pdr = round((totalAck/total)*100,2)
        except ZeroDivisionError:
            pdr = 0
        return {'PDR': pdr, 'tx' :total, 'ack': totalAck}

    def printPDR(self):
        data = {}
        import matplotlib.pyplot as plt
        import io
        import base64
        tempBuffer = io.BytesIO()
        plt.clf()
        data = {}
        index = 2
        for i,j in self.getNodesPDR().items():
            if i < index:
                continue
            try:
                pdr = round((j['ack'] * 100 )/j['tx'],2)
            except ZeroDivisionError:
                pdr = 0
            data[index] = pdr
            index += 1
            width = 0.8
            #plt.text(((index-1) - (width/3)), pdr-2, str(pdr), color="black", fontsize=8)
        tempBuffer = io.BytesIO()
        plt.bar(data.keys(),data.values(), width=width, label="Link Status PDR")
        #plt.bar_label(data.values(), padding=2)
        plt.xticks(list(data.keys()))
        plt.ylim([0, 100])
        plt.xlabel("Nodes")
        plt.ylabel("PDR (%)")
        #plt.legend()
        plt.title("Link-level PDR by node")
        plt.gcf().set_size_inches(8,6)
        plt.savefig(tempBuffer, format = 'png')
        return base64.b64encode(tempBuffer.getvalue()).decode()

class PDR(Base):
    __tablename__ = 'pdrs'
    id = Column(Integer, primary_key=True)
    application = relationship("Application", uselist=False, back_populates="pdr")

    def __init__(self, application) -> None:
        self.application = application


    def processResults(self):
        results = [[] for x in range(self.application.metric.run.maxNodes)]
        for rec in self.application.records:
            if rec.rcv:
                results[rec.srcNode].append(True)
            else:
                results[rec.srcNode].append(False)
        return results
    
    def getGlobalPDR(self):
        totalTrue = 0
        totalFalse = 0
        from collections import Counter
        for i in self.processResults():
            node = Counter(i)
            totalTrue += node[True]
            totalFalse += node[False]
        try:
            return (round(totalTrue/(totalFalse+totalTrue)*100,2))
        except ZeroDivisionError: # Happens when the node never ingress in TSCH
            return 0.0

    def printPDR(self):
        data = {}
        results = self.processResults()
        from collections import Counter
        index = 2
        totalGlobal = 0
        trueGlobal = 0
        import io
        import base64
        import matplotlib.pyplot as plt
        plt.clf()
        for i in results[2:]: # The first is the sink node
            node = Counter(i)
            total = node[True] + node[False]
            totalGlobal += total
            trueGlobal += node[True]
            try:
                pdr = round((node[True]/total)*100,2)
            except ZeroDivisionError: # Happens when the node never ingress in TSCH
                pdr = 0
            #print ("Node" , index ,"Total: " , total, " False: ", node[False])
            #print ("PDR: " , pdr,"%")
            data[index] = pdr
            index += 1
            width = 0.8
            #plt.text(((index-1) - (width/3)), pdr-2, str(pdr), color="black", fontsize=8)
        #print ("PDR Global: ",round((node[True]/total)*100,2))
        tempBuffer = io.BytesIO()
        plt.bar(data.keys(),data.values(), width=width, label="PDR")
        #plt.bar_label(data.values(), padding=2)
        plt.xticks(list(data.keys()))
        plt.ylim([0, 100])
        plt.xlabel("Nodes")
        plt.ylabel("PDR (%)")
        plt.title("Application PDR by node")
        #plt.legend()
        plt.gcf().set_size_inches(8,6)
        plt.savefig(tempBuffer, format = 'png')
        return base64.b64encode(tempBuffer.getvalue()).decode() 

class Latency(Base):
    __tablename__ = 'latencies'
    id = Column(Integer, primary_key=True)
    #application_id = Column(Integer, ForeignKey('application.id')) # The ForeignKey must be the physical ID, not the Object.id
    application = relationship("Application", uselist=False, back_populates="latency") 
    def __init__(self,application) -> None:
        self.application = application

    def getNodes(self):
        nodes = []
        for i in range(self.application.metric.run.maxNodes):
            nodes.append(list())
            #print(len(self.nodes))
        for i in self.application.records:
            if (i.rcv):
                nodes[i.srcNode].append(tuple((i.genTime/1000, i.getLatency()/float(1000))))
        return nodes

    def latencyMean(self):
        from numpy import mean
        nodes = self.getNodes()
        values = []
        for register in nodes:
            for value in register:
                values.append(value[1])
        globalMean = round(mean(values),3)
        return globalMean

    def latencyMedian(self):
        from numpy import median
        nodes = self.getNodes()
        values = []
        for register in nodes:
            for value in register:
                values.append(value[1])
        globalMedian = round(median(values),3)
        return globalMedian

    def getLatencyDataByNode(self):
        myData = {}
        for i in range(2,(self.application.metric.run.maxNodes)):
            myData['N' + str(i)] = []
        for rec in self.application.records:
            if rec.rcv:
                myData['N' + str(rec.srcNode)].append(rec.getLatency()/float(1000))
        return myData

    def getLatencyMedianByNode(self):
        retorno = {}
        for k,v in self.application.latency.getLatencyDataByNode().items():
            retorno[k] = median(v)
        return retorno

    def printLatencyByNode(self):
        import io
        import base64
        import matplotlib.pyplot as plt
        plt.clf()
        tempBuffer = io.BytesIO()
        myData = self.getLatencyDataByNode()
        labels, data = myData.keys(), myData.values()
        plt.boxplot(data)
        plt.xticks(range(1, len(labels) + 1), labels)
        plt.title("Latency (ms)")
        plt.gcf().set_size_inches(8,6)
        plt.savefig(tempBuffer, format = 'png')
        return base64.b64encode(tempBuffer.getvalue()).decode()
        #plt.show()
    
    def printLatencyByNodesPosition(self):
        from mpl_toolkits.mplot3d import Axes3D
        import matplotlib.pyplot as plt
        import io
        import base64
        from numpy import mean
        import matplotlib.cm as cm
        import numpy as np
        tempBuffer = io.BytesIO()
        plt.clf()
        nodes = []
        x = []
        y = []
        z = []
        latData = self.getLatencyDataByNode()
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for node, position in self.application.metric.run.getNodesPosition().items():
            nodes.append(node)
            x.append(position['x'])
            y.append(position['y'])
            try:
                if latData[node] == []: #No Latency Data
                    z.append(0)
                    ax.text(position['x'],position['y']+5, 0, "No Data", )
                else:
                    z.append(mean(latData[node]))
                    #ax.text(position['x'],position['y']+5, mean(latData[node]), mean(latData[node]) )
            except:
                # Node 1
                z.append(0)
        #ax.scatter(x, y, z, c='b', marker='o')
        cmap = cm.get_cmap('rainbow')
        max_height = np.max(z)   # get range of colorbars
        min_height = np.min(z)
        # scale each z to [0,1], and get their rgb values
        rgba = [cmap((k-min_height)/max_height) for k in z]
        ax.bar3d(x, y, 0, 2, 2, z, color=rgba)
        i = 0
        for label in nodes:
            ax.text(x[i],y[i]+2,z[i], label)
            i += 1
        colourMap = plt.cm.ScalarMappable(cmap=plt.cm.rainbow)
        colourMap.set_array(z)
        colBar = plt.colorbar(colourMap).set_label('Latency (ms)')
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        #ax.set_zlabel('Latency (ms)')
        ax.set_title("Nodes latency (Mean)")
        #ax.set_zlim3d(0,100)
        plt.gcf().set_size_inches(8,6)
        plt.savefig(tempBuffer, format = 'png')
        return base64.b64encode(tempBuffer.getvalue()).decode()


    def printLatency(self):
        import io
        import base64
        import matplotlib.pyplot as plt
        plt.clf()
        tempBuffer = io.BytesIO()
        nodes = self.getNodes()
        for i in range(2,self.application.metric.run.maxNodes):
            x = [a[0]/1000 for a in nodes[i]] # Seconds
            y = [round(a[1],3) for a in nodes[i]] # Miliseconds
            plt.plot(x, y,linestyle="",marker=".", label = "Node "+str(i))
        # TODO: Adjust ALL latency units to ms
        myMean = self.latencyMean()
        myMedian = self.latencyMedian()
        plt.axhline(y = myMean, color = 'r', linestyle = '--',label="Mean: " + str(myMean) +' ms')
        plt.axhline(y = myMedian, color = 'g', linestyle = '--',label="Median: " + str(myMedian) +' ms')
        plt.axvline(x=int(self.application.metric.run.parameters['APP_WARM_UP_PERIOD_SEC']), label="Warm-up Time", ls=':', c='Orange')
        plt.xlabel("Simulation Time (s)")
        plt.ylabel("Latency (ms)")
        plt.legend()
        plt.title("Application Latency")
        #plt.show()
        plt.gcf().set_size_inches(8,6)
        plt.savefig(tempBuffer, format = 'png')
        return base64.b64encode(tempBuffer.getvalue()).decode()

class AppRecord(Base):
    __tablename__ = 'apprecords'
    id = Column(Integer, primary_key=True)
    genTime = Column(Integer, nullable=False)
    rcvTime = Column(Integer)
    rcv = Column(Boolean)
    srcNode = Column(Integer, nullable=False)
    dstNode = Column(Integer, nullable=False)
    sqnNumb = Column(Integer, nullable=False)
    application_id = Column(Integer, ForeignKey('application.id')) # The ForeignKey must be the physical ID, not the Object.id
    application = relationship("Application", back_populates="records")

    def __init__(self, genTime, srcNode, dstNode, sqnNumb):
        self.genTime = genTime
        self.srcNode = srcNode
        self.dstNode = dstNode
        self.sqnNumb = sqnNumb
        self.rcv = False

    def rcvPkg(self, rcvTime):
        self.rcvTime = rcvTime
        self.rcv = True

    def getLatency(self):
        return self.rcvTime - self.genTime

class Energy(Base):
    '''
    Energy-related Metrics
    '''
    __tablename__ = 'energy'
    id = Column(Integer, primary_key=True)
    metric = relationship("Metrics", uselist=False, back_populates="energy")
    results = Column(MutableList.as_mutable(PickleType))

    def __init__(self,metric):
        self.metric = metric
        self.results = []
        self.processEnergy()

    def getChannelUtilization(self):
        '''
            The Energest module reports a period each 60 seconds 
            :return: float
        '''
        return pd.DataFrame(self.results).set_index('time')['channel-utilization'].mean()
    
    def getRadioDutyCicle(self):
        '''
            Returns the
            :return: float
        '''

        return pd.DataFrame(self.results).set_index('time')['duty-cycle'].mean()

    def parseEnergest(self, log):
        '''
        method extracted from: https://github.com/contiki-ng/contiki-ng/blob/develop/examples/benchmarks/rpl-req-resp/parse.py
        '''
        res = re.compile('Radio Tx\s*:\s*(\d*)/\s*(\d+)').match(log)
        if res:
            tx = float(res.group(1))
            total = float(res.group(2))
            return {'channel-utilization': 100.*tx/total }
        res = re.compile('Radio total\s*:\s*(\d*)/\s*(\d+)').match(log)
        if res:
            radio = float(res.group(1))
            total = float(res.group(2))
            return {'duty-cycle': 100.*radio/total }
        return None


    #@orm.reconstructor
    def processEnergy(self):
        records = [rec for rec in self.metric.run.records if rec.recordType == "Energest"]
        for rec in records:
            #if rec.recordType == "Energest": # No need because
            parsing = self.parseEnergest(rec.rawData)
            if parsing != None:
                parsing['time'] = rec.simTime
                self.results.append(parsing)
        del records

Experiment.runs = relationship("Run", order_by = Run.id, back_populates="experiment")
Run.records = relationship("Record", order_by = Record.id, back_populates="run")
#Application.records = relationship("AppRecord", order_by = AppRecord.id, back_populates="application")
meta.create_all()
