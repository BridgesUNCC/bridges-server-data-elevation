from app import app
from flask import request
from flask import send_file
import logging
from logging.handlers import RotatingFileHandler
import wget
import os
import subprocess
import math
import hashlib
import pickle
import io
import shutil
import click


round_val = 4
maxMapFolderSize = 1*1024*1024*1024  #change first value to set number of gigabytes the map folder should be
LRU = []
noaa_url = 'https://gis.ngdc.noaa.gov/arcgis/rest/services/DEM_mosaics/ETOPO1_ice_surface/ImageServer/exportImage?bbox='
divider = "-----------------------------------------------------------------"


#bbox=-79.99167,35.95833,-79.62500,36.19167&bboxSR=4326&size=22,14&imageSR=4326&format=tiff&pixelType=S16&interpolation=+RSP_NearestNeighbor&compression=LZW&f=image
#https://gis.ngdc.noaa.gov/arcgis/rest/services/DEM_mosaics/ETOPO1_ice_surface/ImageServer/exportImage?bbox=-82.07500,34.39167,-78.87500,35.92500&bboxSR=4326&size=192,92&imageSR=4326&format=tiff&pixelType=S16&interpolation=+RSP_NearestNeighbor&compression=LZW&f=image
#bbox=-98.08593749997456,36.03133177632377,-88.94531249997696,41.508577297430456
#minlon, minlat, maxlon, maxlat



#35.3123702255912,-80.72571581793821
#35.29678506001799,-80.74595040274656


#Test coords
#minLon=-80.97006&minLat=35.08092&maxLon=-80.6693&maxLat=35.3457
#http://127.0.0.1:5000/elevation?minLon=-80.745950&minLat=35.29678&maxLon=-80.725715&maxLat=35.312370

#https://gis.ngdc.noaa.gov/arcgis/rest/services/DEM_mosaics/ETOPO1_ice_surface/ImageServer/exportImage?bbox=-98.04167,41.02500,-96.95833,42.50833&bboxSR=4326&size=65,89&imageSR=4326&format=tiff&pixelType=S16&interpolation=+RSP_NearestNeighbor&compression=LZW&f=image


#WSEN
#LON,LAT,LON,LAT

# This takes the output of the server and adds the appropriate headers to make the security team happy
def harden_response(message_str):
    response = app.make_response(message_str)
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

@app.route('/elevation')
def ele():
    '''try:
        coord_val = [round(float(request.args['minLat']), round_val), round(float(request.args['minLon']), round_val), round(float(request.args['maxLat']), round_val), round(float(request.args['maxLon']), round_val)]
        #log stuffs
        app_log.info(divider)
        app_log.info(f"Requester: {request.remote_addr}")
        app_log.info(f"Script started with BBox: {request.args['minLat']}, {request.args['minLon']}, {request.args['maxLat']}, {request.args['maxLon']}")
    except:
        print("System arguements are invalid")
        app_log.exception(f"System arguements invalid {request.args}")
        return 'not valid coordinate inputs'

    try:
        res_val = [round(float(request.args['resX']), round_val), round(float(request.args['resY']), round_val)]
        app_log.info(f"Density Resolution: {res_val[0]}, {res_val[1]}")
    except:
        res_val = [.01666, .01666]
    '''
    app_log.info(divider)
    app_log.info(f"Requester: {request.remote_addr}")
    coord_val, res_val = parse_parameters(request.args)
    return harden_response(pipeline(coord_val, res_val))

@app.route('/hash')
def hashreturn():
    '''try:
        coord_val = [round(float(request.args['minLat']), round_val), round(float(request.args['minLon']), round_val), round(float(request.args['maxLat']), round_val), round(float(request.args['maxLon']), round_val)]
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
        res_val = [.01666, .01666]
    '''
    app_log.info(divider)
    app_log.info(f"Requester: {request.remote_addr}")
    coord_val, res_val = parse_parameters(request.args)
    dir = dir_construct(coord_val, res_val)

    try:
        with open(f"{dir}/hash.txt", 'r') as f:
            re = f.readlines()
            app_log.info(f"Hash value found: {re[0]}")
            return harden_response(re[0])
    except Exception as e:
        print("No map hash found")
        print(e)
        return harden_response("false")
 
    return ''
    
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
    file_cleanup()
    return harden_response("Server Error occured while attempting to process your request. Please try again...")

# Returns two lists of parameters(bounding box corrdinates and resolution values) given the arguments
def parse_parameters(args):
    try:
        coord_val = [round(float(args['minLat']), round_val), round(float(args['minLon']), round_val), round(float(args['maxLat']), round_val), round(float(args['maxLon']), round_val)]
        #app_log.info(f"Requester: {request.remote_addr}")
        app_log.info(f"Script started with BBox: {args['minLat']}, {args['minLon']}, {args['maxLat']}, {args['maxLon']}")
    except:
        print("System arguements are invalid")
        app_log.exception(f"System arguements invalid {request.args}")
        return 'not valid coordinate inputs'

    try:
        res_val = [round(float(args['resX']), round_val), round(float(args['resY']), round_val)]
        app_log.info(f"Density Resolution: {res_val[0]}, {res_val[1]}")
    except:
        res_val = [.01666, .01666]
    
    return coord_val, res_val

def url_construct(coords, res):
    url = noaa_url
    #minlon, minlat, maxlon, maxlat
    size = size_calc(coords, res)
    url = url + f"{coords[1]},{coords[0]},{coords[3]},{coords[2]}&bboxSR=4326&size={size[0]},{size[1]}&imageSR=4326&format=tiff&pixelType=S16&interpolation=+RSP_NearestNeighbor&compression=LZW&f=image"
    app_log.info(url)
    return url

def dir_construct(coords, res):
    dir = f"app/elevation_maps/{coords[0]}/{coords[1]}/{coords[2]}/{coords[3]}/{res[0]}/{res[1]}"
    return dir

def size_calc(coords, res):
    yDiff = abs(abs(coords[2]) - abs(coords[0]))
    xDiff = abs(abs(coords[3]) - abs(coords[1]))
    size = [round(xDiff/res[0]), round(yDiff/res[1])]
    return size

def request_map(url, coords):
    filename = wget.download(url, out=f'app')
    return filename

def convert_map(filename):
    command = f"gdal_translate -of AAIGrid {filename} app/data.asc"
    subprocess.run([command], shell=True)
    return "app/data.asc"

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
    map_dir = dir_construct(coords, res)
    if (os.path.isfile(f"{map_dir}/data")):
        f = open(f"{map_dir}/data")
        data = f.read()
        lruUpdate(coords, res)
        f.close()
        return data

    if (res[0] < 0.01666):
        res[0] = .01666
    if(res[1] < 0.01666):
        res[1] = .01666

    data = convert_map(request_map(url_construct(coords, res), coords))
    try:
        os.makedirs(f'{map_dir}')
    except:
        pass
    
    os.rename(f'{data}', f'{map_dir}/data')
    if (os.path.isfile(f"{map_dir}/data")):
        f = open(f"{map_dir}/data")
        data = f.read()
        f.close()
        lruUpdate(coords, res)
        

    try:
        md5_hash = hashlib.md5()
        with open(f"{map_dir}/data","rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096),b""):
                md5_hash.update(byte_block)
            app_log.info("Hash: " + md5_hash.hexdigest())
        with open(f"{map_dir}/hash.txt", "w") as h:
            h.write(md5_hash.hexdigest())
    except Exception as e:
        app_log.exception(f"Hashing error occured: {e}")
    

    #file cleanup
    file_cleanup()

    return data


def file_cleanup():
    #file cleanup
    try:
        if os.path.exists('app/exportImage'):
            os.remove('app/exportImage')
        if os.path.exists('app/data.prj'):
            os.remove('app/data.prj')
        if os.path.exists('app/data.asc.aux.xml'):
            os.remove('app/data.asc.aux.xml')
    except:
        app_log.info("Error cleaning up temp files")
    return

@app.cli.command('wipe')
def wipe_cache():
    try:
        shutil.rmtree('app/elevation_maps')
        os.mkdir('app/elevation_maps')
        os.remove('lru.txt')
    except:
        pass

#setting up the server log
app_log = logging.getLogger('elev-logger')
app_log.setLevel(logging.DEBUG)

formatt = logging.Formatter('%(asctime)s %(message)s')

fh = logging.FileHandler('log.log', mode='a')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatt)
app_log.addHandler(fh)


'''
format = logging.Formatter('%(asctime)s %(message)s')   #TODO: Logger not logging

logFile = 'log.log'
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(format)
my_handler.setLevel(logging.DEBUG)


app_log.addHandler(my_handler)
'''
try:
    with open("lru.txt", "rb") as fp:
        LRU = pickle.load(fp)
except:
    pass