from app import app
from flask import request
import logging
from logging.handlers import RotatingFileHandler
import wget
import os
import math
import hashlib
import pickle
import io
import shutil

round_val = 4
maxMapFolderSize = 1*1024*1024*1024  #change first value to set number of gigabytes the map folder should be
LRU = []
noaa_url = 'https://gis.ngdc.noaa.gov/mapviewer-support/wcs-proxy/wcs.groovy?filename=etopo1.xyz&request=getcoverage&version=1.0.0&service=wcs&coverage=etopo1&CRS=EPSG:4326&format=xyz&'
divider = "-----------------------------------------------------------------"



#https://gis.ngdc.noaa.gov/mapviewer-support/wcs-proxy/wcs.groovy?filename=etopo1.xyz&request=getcoverage&version=1.0.0&service=wcs&coverage=etopo1&CRS=EPSG:4326&format=xyz&resx=0.016666666666666667&resy=0.016666666666666667&bbox=-98.08593749997456,36.03133177632377,-88.94531249997696,41.508577297430456
#bbox=-98.08593749997456,36.03133177632377,-88.94531249997696,41.508577297430456
#minlon, minlat, maxlon, maxlat

#Test coords
#minLon=-80.97006&minLat=35.08092&maxLon=-80.6693&maxLat=35.3457

# This takes the output of the server and adds the appropriate headers to make the security team happy
def harden_response(message_str):
    response = app.make_response(message_str)
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

@app.route('/elevation')
def ele():
    try:
        coord_val = [round(float(request.args['minLon']), round_val), round(float(request.args['minLat']), round_val), round(float(request.args['maxLon']), round_val), round(float(request.args['maxLat']), round_val)]
        #log stuffs
        app_log.info(divider)
        app_log.info(f"Requester: {request.remote_addr}")
        app_log.info(f"Script started with BBox: {request.args['minLon']}, {request.args['minLat']}, {request.args['maxLon']}, {request.args['maxLat']}")
    except:
        print("System arguements are invalid")
        app_log.exception(f"System arguements invalid {request.args}")
        return 'not valid coordinate inputs'

    try:
        res_val = [round(float(request.args['resX']), round_val), round(float(request.args['resY']), round_val)]
        app_log.info(f"Density Resolution: {res_val[0]}, {res_val[1]}")
    except:
        res_val = density_calc(coord_val)
        
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

def density_calc(coords):
    yDiff = abs(abs(coords[2]) - abs(coords[0]))
    xDiff = abs(abs(coords[3]) - abs(coords[1]))
    den = [xDiff/100, yDiff/100]
    return den

def request_map(url, coords):
    filename = wget.download(url, out=f'app/elevation_maps')
    return filename



def getFolderSize():
    ''' Calculates the size of the maps folder
        Returns:
            int: size of app/elevation_maps folder in bytes
    '''
    try:
        size = 0
        start_path = 'app/elevation_maps'  # To get size of directory
        for path, dirs, files in os.walk(start_path):
            for f in files:
                fp = os.path.join(str(path), str(f))
                size = size + os.path.getsize(fp)
        return size
    except Exception as e:
        return (e)

def lruUpdate(location, level):
    ''' Updates the LRU list and storage file
        Parameters:
            location(list[float]): a maps bounding box
            level(string): the level of detail a map hash
        Return:
            None
    '''
    try: # Removes the location requested by the API from the LRU list
        LRU.remove([location[0], location[1], location[2], location[3], level])
    except:
        pass
    #Adds in the requested location into the front of the list
    LRU.insert(0, [location[0], location[1], location[2], location[3], level])
    #Removes old maps from server while the map folder is larger than set limit
    while (getFolderSize() > maxMapFolderSize):
        #Removes map from server
        try:
            re = LRU[len(LRU)-1]
            if (os.path.isdir(f"app/elevation_maps/{re[0]}/{re[1]}/{re[2]}/{re[3]}/{re[4]}")):
                shutil.rmtree(f"app/elevation_maps/{re[0]}/{re[1]}/{re[2]}/{re[3]}/{re[4]}")
                del LRU[len(LRU)-1]
        except:
            print("ERROR Deleteing map File")
    #updates the LRU file incase the server goes offline or restarts
    with open("lru.txt", "wb") as fp:   #Pickling
        pickle.dump(LRU, fp)
    return



def pipeline(coords, res):
    dir = f"app/elevation_maps/{coords[0]}/{coords[1]}/{coords[2]}/{coords[3]}"
    if (os.path.isfile(f"{dir}/data")):
        f = open(f"{dir}/data")
        return f

    data = request_map(url_construct(coords, res), coords)
    os.mkdir(f'{dir}')
    os.rename(f'app/{data}', f'{dir}/data')
    if (os.path.isfile(f"{dir}/data")):
        f = open(f"{dir}/data")
        return f

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