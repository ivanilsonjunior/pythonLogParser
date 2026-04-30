import re
import os
import threading

import zipfile
from flask import Flask, render_template, Response, jsonify, request, redirect, send_file
from werkzeug.utils import secure_filename
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

from Model import db, Session, Experiment, Run, Metrics, ProjectConfFile, AVAILABLE_METRICS, DBName, memConnection, memEngine, engine, bulk_status

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

@app.route('/experiment/bulk/<id>', methods=['GET'])
@auth.login_required
def showBulkRun(id):
    exp = db.query(Experiment).filter_by(id=id).first()
    return render_template("bulkRun.html", exp=exp, user=auth.current_user())

@app.route('/experiment/bulk/<id>', methods=['POST'])
@auth.login_required
def executeBulkRun(id):
    slotframe_raw = request.form.get('slotframe_values', '')
    send_interval_raw = request.form.get('send_interval_values', '')
    repetitions = int(request.form.get('repetitions', 1))
    warm_up = request.form.get('warm_up', '300').strip()

    slotframe_values = [v.strip() for v in slotframe_raw.split(',') if v.strip()]
    send_interval_values = [v.strip() for v in send_interval_raw.split(',') if v.strip()]

    exp = db.query(Experiment).filter_by(id=id).first()

    if not slotframe_values or not send_interval_values:
        return render_template("bulkRun.html", exp=exp, user=auth.current_user(),
                               error="Informe ao menos um valor para cada parâmetro.")

    if exp.confFile is None:
        conf = ProjectConfFile()
        conf.defines = {}
        exp.confFile = conf
        db.add(conf)
        db.commit()

    exp.confFile.defines['APP_WARM_UP_PERIOD_SEC'] = warm_up
    db.commit()

    dictVariations = {
        'TSCH_SCHEDULE_CONF_DEFAULT_LENGTH': slotframe_values,
        'APP_SEND_INTERVAL_SEC': send_interval_values,
    }
    bulk_status['experiment_id'] = id

    def run():
        exp = db.query(Experiment).filter_by(id=id).first()
        exp.bulkRun(dictVariations, repetitions)

    process = threading.Thread(target=run)
    process.start()
    return redirect('/experiment/bulk/progress')

@app.route('/experiment/bulk/progress', methods=['GET'])
@auth.login_required
def showBulkProgress():
    return render_template("bulkProgress.html", user=auth.current_user())

@app.route('/experiment/bulk/progress/status', methods=['GET'])
@auth.login_required
def getBulkProgress():
    sim_progress = 0
    sim_to_end = 0
    if os.path.exists('COOJA.log'):
        try:
            with open('COOJA.log', 'r') as f:
                for line in f.readlines():
                    try:
                        data = line.split('-')[1].strip()
                    except IndexError:
                        continue
                    if data.find('completed') != -1:
                        m = re.compile(r'(\d+.\d+|\d+)% completed,\s+(\d+.\d+|\d+) sec remaining').match(data)
                        if m:
                            sim_progress = int(float(m.group(1)))
                            sim_to_end = m.group(2)
                    if data.startswith('Timeout') or data.startswith('TEST OK'):
                        sim_progress = 100
                        sim_to_end = 0
        except Exception:
            pass
    return jsonify({
        'running': bulk_status['running'],
        'current': bulk_status['current'],
        'total': bulk_status['total'],
        'experiment_id': bulk_status['experiment_id'],
        'error': bulk_status['error'],
        'sim_progress': sim_progress,
        'sim_to_end': sim_to_end,
    })

@app.route('/experiment/csv/<id>', methods=['GET'])
@auth.login_required
def showCsvExport(id):
    exp = db.query(Experiment).filter_by(id=id).first()
    runs_with_params = [r for r in exp.runs if r.parameters and r.metric]
    sf_values = sorted({r.parameters['TSCH_SCHEDULE_CONF_DEFAULT_LENGTH'] for r in runs_with_params})
    si_values = sorted({r.parameters['APP_SEND_INTERVAL_SEC'] for r in runs_with_params})
    return render_template("expCsv.html", exp=exp, user=auth.current_user(),
                           run_count=len(runs_with_params),
                           sf_values=sf_values, si_values=si_values,
                           available_metrics=AVAILABLE_METRICS)

@app.route('/experiment/csv/<id>', methods=['POST'])
@auth.login_required
def generateCsv(id):
    import io as _io
    exp = db.query(Experiment).filter_by(id=id).first()
    filename = request.form.get('filename', f'experiment_{id}.csv').strip()
    if not filename.endswith('.csv'):
        filename += '.csv'

    selected = set(request.form.getlist('metrics'))
    if not selected:
        selected = None  # fallback to defaults

    exp.toCsv(filename, selected)

    zip_buffer = _io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in [filename, 'STD' + filename]:
            if os.path.exists(f):
                zf.write(f)
    zip_buffer.seek(0)

    return send_file(zip_buffer, mimetype='application/zip',
                     as_attachment=True,
                     download_name=filename.replace('.csv', '_export.zip'))

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
