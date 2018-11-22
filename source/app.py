from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from patch import *
from utils import *
# LOGGING
from logging.config import dictConfig
logLevel = iif(DEBUG, 'DEBUG', 'INFO')
dictConfig({
    'version': 1,
    'formatters': {
        'default': {'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',},
        'hiformat': {'format': 'HI %(asctime)s - %(module)s - %(levelname)s - %(message)s',},
        'simple': {'format': '%(asctime)s - %(module)s - %(levelname)s - %(message)s',},
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': logLevel,
            'formatter': 'hiformat',
            'stream': 'ext://sys.stdout',
        },
        'file':{
            'level': logLevel,
            'formatter': 'simple',
            'filename': 'logs/app.log',
            'class': 'logging.FileHandler', # handler
            # 'class': 'logging.RotatingFileHandler', # handler
            # 'maxBytes': 10*1024*1024,
            # 'backupCount': 10,
            # 'class': 'logging.TimedRotatingFileHandler', #handler 
            # 'path' : 'logs/app.log',
            # 'when' : "m", #second (s),minute (m),hour (h),day (d),w0-w6 (weekday, 0=Monday),midnight
            # 'interval': 1,
            # 'backupCount': 10
        },
    },
    'loggers':{
        'console':{
            'level': logLevel,
            'handlers': ['console'],
            'propagate': 'no',
        },
        'file':{
            'level': logLevel,
            'handlers': ['file'],
            'propagate': 'no',
        }
    },
    'root': {
        'level': logLevel,
        # 'handlers': ['wsgi', 'console', 'file']
        'handlers': ['wsgi', 'file']
    }
})


app = Flask(__name__)


db_config = readODBC()
# database uri
db_api = "%(DBTYPE)s://%(USER)s:%(PASS)s@%(ODBC)s:%(PORT)s/%(DBNAME)s" % db_config
app.config['SQLALCHEMY_DATABASE_URI'] = db_api
db = SQLAlchemy(app)

class Patch(db.Model):
    __tablename__ = 'tblpatch'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    descr = db.Column(db.String(8000))
    version = db.Column(db.String(255))
    buildno = db.Column(db.String(255))
    patchtype = db.Column(db.Integer())
    lastupdatetime = db.Column(db.DateTime())
    creationtime = db.Column(db.DateTime())
    isdeleted = db.Column(db.Integer())
    patch = db.Column(db.Text())
    rpatch = db.Column(db.Text())


@app.route("/", methods=["GET", "POST"])
def index():
    return json_response(json.dumps('Patch-Minion welcome you :)'), 200)

@app.route("/patch", methods=["GET"])
def patch_status():
    # print ">>> GET <<<"
    ret = get_running_patch_status(request, app.logger)
    return json_response(json.dumps(ret), 200)

@app.route("/patch", methods=["POST"])
def apply_patch():
    # print ">>> POST <<<", os.getcwd()
    if request.content_type != JSON_MIME_TYPE:
        app.logger.debug("Invalid Content Type ")
        error = json.dumps({'msg': 'Invalid Content Type'})
        return json_response(error, 400)
    
    ### Calling main patching handler function
    status_code, ret_ = patch(request, app.logger, PatchInfoDB=Patch)
    return json_response(json.dumps(ret_), status_code)

if __name__ == "__main__":
    port="";next_=0
    for arg in sys.argv:
        _check = 0
        if next_:_check = safe_int(str(arg))
        elif str(arg).startswith('-p'):
            _check=safe_int(str(arg).replace('-p', ''));next_=1
        if 1000 <=_check <= 9999:
            port=_check;break
    if not port:port=8082
    app.run(debug=DEBUG, host="0.0.0.0", port=port)

