#!/usr/bin/python3

#
# Copyright (C) 2020, Humanitarian OpenstreetMap Team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import sys
import ODKForm
import ODKInstance
import argparse
# import csv
from osmfile import OsmFile
import glob
import yaml
import logging
from fastkml import kml
#from shapely.geometry import Point, LineString, Polygon
import epdb                      # FIXME: remove later

#This program scans the top level directory for ODK data files as produced
#by the ODKCollect app for Android. Each XLSForm type gets it's own output
#file containing all the waypoints entered using that form.
#        """)
#        quit()

# The logfile contains multiple runs, so add a useful delimiter
logging.info("-----------------------\nStarting:")

ap = argparse.ArgumentParser()
ap.add_argument("-v", "--verbose",nargs="?",const="0",help="verbose output")
ap.add_argument("-i", "--indir",default="/tmp/odk/",help="input Directory (defaults to /tmp/odk)")
ap.add_argument("-x", "--xform",required=True,help="XForm filename ")
ap.add_argument("-o", "--outdir",help="Output Directory (defaults to indir)")
ap.add_argument("-f", "--format",help="Output format (defaults to osm)")
args = vars(ap.parse_args())

# if verbose, dump to the terminal as well as the logfile.
if not args['verbose']:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)



indir = args['indir']
inform = indir + "forms/" + args['xform'] + ".xml"
handle = open(inform)
logging.info("Opened %s" % inform)
if not args['outdir']:
    outdir = args['indir']
else:
    outdir = args['outdir']
indata = indir + "instances/" + args['xform']
files = glob.glob(indata + "*.xml")
print("FILES: %r" % files)
outfile = outdir + args['xform'] + ".osm"
odkform = ODKForm.ODKForm()
xform = odkform.parse(handle)
odkform.dump()

odkinst = ODKInstance.ODKInstance(files[0])
data = odkinst.parse(files[0], odkform)
# odkinst.dump()
osm = OsmFile(filespec=outfile)
osm.header()

with open("icepark.yaml", "r") as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    print(yaml.dump(cfg))
    
for obj in data:
    # obj.dump()
    node = osm.createObject(obj)
    osm.write(node)

osm.footer()

quit()

# if format == 'osm':
#     osm = OsmFile(args, outdir + '/' + outfile)
#     osm.header()
#     # elif format == 'csv':
#     #     csvfile = open('/tmp/' + form + '.csv', 'w', newline='')
#     #     outfile = open(outdir + '/' + form + ".csv", 'w')
#     # elif format == 'kml':
#     #     ns = '{http://www.opengis.net/kml/2.2}'
#     #     kmlfile = kml.KML()
#     #     outfile = open(outdir + '/' + form + ".kml", 'w')

#     pattern = fullpath + "/" + form[0] + "*"
#     odkdirs = glob.glob(pattern)
#     list.sort(odkdirs)
#     import epdb; epdb.set_trace()
#     for xmldir in odkdirs:
#         logging.info("Opening directory " + xmldir)
#         # FIXME: Ignore the *-media directories.
#         for xmlfile in glob.glob(xmldir + "/*.xml"):
#             if os.path.isfile(xmlfile):
#                 logging.info("Opening XML file " + xmlfile)
#                 data = parse(xmlfile, form)
#                 print("DATA: " + data)
#                 if data != False:
#                     attrs = dict()
#                     if len(data['GPS']):
#                         attrs['lat'] = data['GPS'][0]
#                         attrs['lon'] = data['GPS'][1]
#                         attrs['ele'] = data['GPS'][2]
#                         #osm.node(data['GPS'][0], data['GPS'][1], data['TAGS'])
#                         entry = osm.createNode(attrs, modified=False)
#                         osm.writeWay(entry[0])
#                     else:
#                         logging.warning(" has no GPS coordinates")

#     if format == 'osm':
#         osm.footer()

print("Input files in directory: %s/{forms,instances}" % args.get('indir'))
print("Output file: %s" % outfile)
