# Elevation-Data-Server
Repository for the backend request handling of elevation data for the BRIDGES project

The elevation data server for BRIDGES takes in a bounding box and returns an ArcGIS ascii grid formatted set of elevation values. This server is powered by the [NOAA Grid Extraction tool](https://www.ngdc.noaa.gov/mgg/global/) and uses the ETOPO1 elevation map with a resolution of 1 arc minute.

## Running this Server
### Python Library Requirements
    - flask
    - wget
    
### Unix Library Dependencies
    - gdal-bin

### Launching the Server
From the servers main directory run the command
```bash
flask run --host=0.0.0.0 --port=8080
```
### Clearing Cached Elevation Files
From the servers main directory run the command
```bash
flask wipe
```



## Making Requests
The structure for making elevation data requests is as followed (using this will use the default resoultion values of 1 arc min or .0166)
```html
https://cci-bridges-elevation-t.uncc.edu/elevation?minLon=6.0205581&minLat=46.10757&maxLon=9.707863&maxLat=47.77059
```



### The resolution of a map is what each incriment will be on the x and y axis. 

To use your own resolution values format it like
```html
https://cci-bridges-elevation.uncc.edu/elevation?minLon=6.0205581&minLat=46.10757&maxLon=9.707863&maxLat=47.77059&resX=.01&resY=.01
```
## Data Return Format
```
ncols        20
nrows        4
xllcorner    -98.496982307692
yllcorner    41.031300000000
cellsize     0.022727692308
 591 588 580 575 575 577 571 560 528 535 546 528 546 514 516 496 471 473 497 487 
 496 504 500 502 497 491 488 510 524 522 533 536 527 532 540 542 542 548 548 557
 544 534 545 539 545 552 533 532 522 511 499 492 482 490 500 494 486 465 470 481
 476 464 453 460 456 480 482 474 458 471 460 421 407 393 421 421 393 404 415 388
```

## Examples
    * 36.8241, -116.8369, 35.7797, -117.4074    (Death Valley)
    * 49.0872, -113.6184, 47.3746, -114.8143    (Glacier National Park)
    * 40.1924, -79.3980, 37.5021, -81.8810      (West Virginia)
