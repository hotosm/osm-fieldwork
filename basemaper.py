#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
#
# This file is part of Odkconvert.
#
#     Odkconvert is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Odkconvert is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Odkconvert.  If not, see <https:#www.gnu.org/licenses/>.
#

import argparse
import os
import logging
import sys
import epdb
import geojson
from sys import argv
import mercantile
from osgeo import ogr
from pySmartDL import SmartDL
from cpuinfo import get_cpu_info
from codetiming import Timer
import queue
import concurrent.futures
import threading


def dlthread(dest, mirrors, tiles):
    """Thread to handle downloads for Queue"""
    # counter = -1
    errors = 0

    # start = datetime.now()

    # totaltime = 0.0
    logging.info("Downloading %d tiles in thread %d to %s" % (len(tiles), threading.get_ident(), dest))
    for tile in tiles:
        filespec = f"{tile[2]}/{tile[1]}/{tile[0]}.png"
        for site in mirrors:
            url = site['url']
            remote = url % (tile[2], tile[1], tile[0])
            print("FIXME: %s" % remote)
            # Create the subdirectories as pySmartDL doesn't do it for us
            if os.path.isdir(dest) is False:
                tmp = ""
                paths = dest.split('/')
                for i in paths[1:]:
                    tmp += '/' + i
                    if os.path.isdir(tmp):
                        continue
                    else:
                        os.mkdir(tmp)
                        logging.debug("Made %s" % tmp)

        try:
            if not os.path.exists(dest + "/" + filespec):
                dl = SmartDL(remote, dest=dest + "/" + filespec, connect_default_logger=False)
                dl.start()
            else:
                logging.debug("%s exists!" % (dest + "/" + filespec))
        except:
            logging.error("Couldn't download from %r: %s" %  (filespec, dl.get_errors()))
        #     errors += 1
        #     continue

    #         if dl.isSuccessful():
    #             if dl.get_speed() > 0.0:
    #                 logging.info("Speed: %s" % dl.get_speed(human=True))
    #                 logging.info("Download time: %r" % dl.get_dl_time(human=True))
    #             totaltime +=  dl.get_dl_time()
    #             # ERSI does't append the filename
    #             totaltime +=  dl.get_dl_time()
    #             suffix = filetype.guess(dl.get_dest())
    #             print('File extension: %s' % suffix.extension)
    #             if suffix.extension == 'jpg':
    #                 os.rename(dl.get_dest(), filespec)
    #                 logging.debug("Renamed %r" % dl.get_dest())
    #                 ext = ".jpg"  # FIXME: probably right, but shouldbe a better test
    #             else:
    #                 ext = tmp[1]
    #                 counter += 1

    #         counter += 1
    #         db.createVRT(filespec, tile)

    # end = datetime.now()
    # delta = start - end
    # logging.debug("%d errors out of %d tiles" % (errors, len(tiles)))
    # # logging.debug("Processed %d tiles in %d.%d.%d minutes" % (len(tiles), delta.minutes , delta.microseconds))

class BaseMapper(object):
    def __init__(self, filespec=None, base=None, source=None):
        """Create an mbtiles basemap for ODK Collect"""
        geom = ogr.Open(filespec)
        layer = geom.GetLayer()
        self.bbox = self.makeBbox(layer)
        self.tiles = list()
        self.base = base
        # sources for imagery
        self.source = source
        self.sources = dict()
        # quad ?
        url = "http://ecn.t0.tiles.virtualearth.net/tiles/h%s.png?g=129&mkt=en&stl=H"
        source = {'name': "Bing Maps Hybrid", 'url': url}
        self.sources['bing'] = source

        # zoom, y, x
        url = "http://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/%d/%d/%d.png"
        source = {'name': "ESRI World Imagery", 'url': url}
        self.sources['ersi'] = source
        
    def getTiles(self, zoom=None):
        """Get a list of tiles for the specifed zoom level"""
        if not zoom:
            return False

        info = get_cpu_info()
        cores = info['count']

        self.tiles = list(mercantile.tiles(self.bbox[0], self.bbox[1], self.bbox[2], self.bbox[3], zoom))
        total = len(self.tiles)        
        logging.info("%d tiles for zoom level %d" % (len(self.tiles), zoom))
        chunk =  round(len(self.tiles)/cores)
        threads = queue.Queue(maxsize=cores)
        logging.info("%d threads, %d tiles" % (cores, total))

        mirrors = [self.sources[self.source]]
        #epdb.st()
        dlthread(self.base, mirrors, self.tiles[0:10])
        with concurrent.futures.ThreadPoolExecutor(max_workers=cores) as executor:
            block = 0
            while block <= len(self.tiles):
                future = executor.submit(dlthread, self.base, mirrors, self.tiles[block:block+chunk])
                logging.debug("Dispatching Block %d:%d" % (block, block + chunk))
                block += chunk
            executor.shutdown()
            # logging.info("Had %r errors downloading %d tiles for data for %r" % (self.errors, len(tiles), os.path.basename(self.base)))

        return True

    def downloadTile(self, source=None, tile=list()):
        pass        
        return True

    def tileExists(self, tile=list()):
        """See if a map tile already exists"""
        filespec = f"{self.base}{tile[2]}/{tile[1]}/{tile[0]}.png"
        if os.path.exists(filespec):
            logging.debug("%s exists" % filespec)
            return True
        else:
            logging.debug("%s doesn't exists" % filespec)
            return False
    
    def makeBbox(self, layer=None):
        """Make a bounding box from a layer"""
        # left, bottom, right, top
        # minX: %d, minY: %d, maxX: %d, maxY: %d" %(env[0],env[2],env[1],env[3])
        for feature in layer:
            bbox = list(feature.GetGeometryRef().GetEnvelope())
            bbox = (bbox[0],bbox[2],bbox[1],bbox[3])
            print(bbox)
        return bbox

    def writeMbtiles(self, filespec):
        """Write the tiles to an mbtiles file"""
        logging.info("Wrote map tiles to %s" % filespec)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create an mbtiles basemap for ODK Collect')
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-b", "--boundary", help='The boundary for the area you want')
    parser.add_argument("-z", "--zooms", default="12-17", help='The Zoom levels')
    parser.add_argument("-t", "--tiles", help='Top level directory for tile cache')
    parser.add_argument("-o", "--outfile", help='Output file name')
    parser.add_argument("-s", "--source", default="ersi", choices=["ersi", "bing", "topo"], help='Imagery source')
    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)


# Get all the zoom levels we want
zooms = list()
if args.zooms:
    if args.zooms.find("-") > 0:
        start = int(args.zooms.split('-')[0])
        end = int(args.zooms.split('-')[1])
        x = range(start, end)
        for i in x:
            zooms.append(i)
    elif args.zooms.find(",") > 0:
        levels = args.zooms.split(',')
        for level in levels:
            zooms.append(int(level))
    else:
        zooms.append(int(args.zooms))

# Make a bounding box from the boundary file
if not args.boundary:
    logging.error("You need to specify a boundary file!")
    parser.print_help()
    quit()

base = "/tmp/foo"
if args.source:
    basemap = BaseMapper(args.boundary, base, args.source)
else:
    logging.error("You need to specify a source!")
    quit()

for level in zooms:
    basemap.getTiles(level)

if args.outfile:
    basemap.writeMbtiles(args.outfile)
else:
    logging.error("You need to specify an outfile filename!")
