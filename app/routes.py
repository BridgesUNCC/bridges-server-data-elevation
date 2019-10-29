from app import app
from flask import request
import logging
from logging.handlers import RotatingFileHandler
import wget

round_val = 4
noaa_url = 'https://gis.ngdc.noaa.gov/mapviewer-support/wcs-proxy/wcs.groovy?filename=etopo1.xyz&request=getcoverage&version=1.0.0&service=wcs&coverage=etopo1&CRS=EPSG:4326&format=xyz&'

#https://gis.ngdc.noaa.gov/mapviewer-support/wcs-proxy/wcs.groovy?filename=etopo1.xyz&request=getcoverage&version=1.0.0&service=wcs&coverage=etopo1&CRS=EPSG:4326&format=xyz&resx=0.016666666666666667&resy=0.016666666666666667&bbox=-98.08593749997456,36.03133177632377,-88.94531249997696,41.508577297430456
#bbox=-98.08593749997456,36.03133177632377,-88.94531249997696,41.508577297430456
#minlon, minlat, maxlon, maxlat

# This takes the output of the server and adds the appropriate headers to make the security team happy
def harden_response(message_str):
    response = app.make_response(message_str)
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

@app.route('/elevation')
def ele():
    try:
        coord_val = [round(float(request.args['minLon']), round_val), round(float(request.args['minLat']), round_val), round(float(request.args['maxLon']), round_val), round(float(request.args['maxLat']), round_val))]
        res_val = []
        #log stuffs
        app_log.info(divider)
        app_log.info(f"Requester: {request.remote_addr}")
        app_log.info(f"Script started with BBox: {request.args['minLon']}, {request.args['minLat']}, {request.args['maxLon']}, {request.args['maxLat']}")
    except:
        print("System arguements are invalid")
        app_log.exception(f"System arguements invalid {request.args}")
        return 'not valid coordinate inputs'

    return harden_response(pipeline(coord_val, res_val))
    

@app.route('/favicon.ico')
def icon():
    return ''

@app.route('/')
def noinput():
    return harden_response(page_not_found())

@app.errorhandler(404)
def page_not_found(e=''):
    return harden_response("Not a valid URL")

@app.errorhandler(500)
def server_error(e=''):
    return harden_response("Server Error occured while attempting to process your request. Please try again...")

def url_construct(coords, res):
    url = noaa_url
    #minlon, minlat, maxlon, maxlat
    url = url + f"resx={res[0]}&resy={res[1]}&bbox={coords[0]},{coords[1]},{coords[2]},{coords[3]}"
    return url

def request_map(url):
    filename = wget.download(url, out="")
    return data

def pipeline(coords, res):
    
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