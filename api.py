import re
import os
import threading

from flask import Flask, render_template, Response, jsonify, request, redirect
from werkzeug.utils import secure_filename
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

from Model import db, Session, Experiment, Run, Metrics, DBName, memConnection, memEngine, engine

auth = HTTPBasicAuth()

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "letmein")

users = {
    "admin": generate_password_hash(ADMIN_PASSWORD)
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username

app = Flask(__name__, template_folder="templates")
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.sql']
app.config['UPLOAD_PATH'] = 'uploads/'

@app.teardown_appcontext
def shutdown_session(exception=None):
    if exception:
        Session.rollback()
    Session.remove()

@app.route('/')
def hello():
    exp = db.query(Experiment).all()
    qtd = len(exp)
    return render_template("index.html", count=qtd, experiments=exp)

@app.route('/experiment/<id>')
def detailExperiment(id):
    exp = db.query(Experiment).filter_by(id=id).first()
    return render_template("expDetail.html", exp=exp)

def runExperiment(id):
    db.query(Experiment).filter_by(id=id).first().run()

@app.route('/experiment/run/<id>')
@auth.login_required
def showRunStatus(id):
    process = threading.Thread(target=runExperiment, args=(id,))
    process.start()
    return render_template("run.html", user=auth.current_user())

@app.route('/experiment/run/progress')
@auth.login_required
def getProgress():
    isRun = False
    progress = 0
    toEnd = 999999999
    with open("COOJA.log", "r") as f:
        for line in f.readlines():
            try:
                data = line.split('-')[1].strip()
            except IndexError:
                continue
            if data.startswith('Script timeout in'):
                isRun = True
            if data.find('completed') != -1:
                exp = re.compile(r'(\d+.\d+|\d+)% completed,\s+(\d+.\d+|\d+) sec remaining').match(data)
                progress = int(float(exp.group(1)))
                toEnd = exp.group(2)
            if data.startswith('Timeout'):
                toEnd = 0
                progress = 100
            if data.startswith('TEST OK'):
                isRun = False
    
    # Count lines in COOJA.testlog, handling if file doesn't exist
    log = 0
    testlog_path = 'COOJA.testlog'
    if os.path.exists(testlog_path):
        with open(testlog_path, 'r') as f:
            log = len(f.readlines())
    
    status = {'run': isRun, 'progress': progress, 'doneIn': toEnd, 'logFile': log}
    return jsonify(status)

@app.route('/experiment/run/<id>/metrics')
@auth.login_required
def extractMetricFromRun(id):
    run = db.query(Run).filter_by(id=id).first()
    run.metric = Metrics(run)
    db.commit()
    return render_template("runDetail.html", run=run, user=auth.current_user())

@app.route('/experiment/add/', methods=['GET'])
@auth.login_required
def showExperimentAdd():
    experiments = db.query(Experiment).all()
    qtd = len(experiments)
    csc_files = sorted(f for f in os.listdir('.') if f.endswith('.csc'))
    return render_template("expAdd.html", count=qtd, experiments=experiments, user=auth.current_user(), csc_files=csc_files)

@app.route('/experiment/add/', methods=['POST'])
@auth.login_required
def executeExperimentAdd():
    expName = request.form['expName']
    expFile = request.form['expFile']
    exp = Experiment(name=expName, experimentFile=expFile)
    db.add(exp)
    db.commit()
    experiments = db.query(Experiment).all()
    qtd = len(experiments)
    csc_files = sorted(f for f in os.listdir('.') if f.endswith('.csc'))
    return render_template("expAdd.html", count=qtd, experiments=experiments, user=auth.current_user(), csc_files=csc_files)

@app.route('/run/<id>')
def detailRun(id):
    run = db.query(Run).filter_by(id=id).first()
    hasMetric = False
    if run.metric is None:
        hasMetric = True
    return render_template("runDetail.html", run=run, hasMetric=hasMetric)

@app.route('/run/summary/<id>')
def summaryRun(id):
    run = db.query(Run).filter_by(id=id).first()
    return render_template("runSummary.html", run=run)

@app.route('/metrics/slotframe/<size>')
def metricBySlotFrame(size):
    retorno = []
    runs = db.query(Run).all()
    for r in runs:
        parameters = r.parameters
        if parameters['TSCH_SCHEDULE_CONF_DEFAULT_LENGTH'] == size:
            retorno.append(r)
    return render_template("metricSlotFrame.html", id=size, retorno=retorno)

@app.route('/metrics/sendrate/<interval>')
def metricBySendInterval(interval):
    retorno = []
    runs = db.query(Run).all()
    for r in runs:
        parameters = r.parameters
        if parameters['APP_SEND_INTERVAL_SEC'] == interval:
            retorno.append(r)
    return render_template("metricSentInterval.html", id=interval, retorno=retorno)

@app.route('/admin/db/show', methods=['GET'])
@auth.login_required
def showDB():
    global engine
    print("Engine:", engine)
    exp = db.query(Experiment).all()
    qtd = len(exp)
    return render_template("index.html", count=qtd, experiments=exp)

@app.route('/admin/db/switch', methods=['GET'])
@auth.login_required
def switchDB():
    import sqlite3
    global engine
    print("Engine:", engine)
    exp = db.query(Experiment).all()
    qtd = len(exp)
    fisico = sqlite3.connect(DBName)
    fisico.backup(memConnection)
    engine = memEngine
    return render_template("index.html", count=qtd, experiments=exp)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=9001, debug=True)
