from app import app
from flask import request

@app.route('elevation')
def ele():

    return


def pipeline():
    try:
        input_val = [request.args['minlat'], request.args['minlon'], request.args['maxlat'], request.args['maxlon']]


    return


#setting up the server log
format = logging.Formatter('%(asctime)s %(message)s')
logFile = 'log.log'
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(format)
my_handler.setLevel(logging.INFO)

app_log = logging.getLogger('root')
app_log.setLevel(logging.DEBUG)

app_log.addHandler(my_handler)