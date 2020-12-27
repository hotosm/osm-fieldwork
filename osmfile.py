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

import logging
import string
import epdb
from datetime import datetime
import ODKInstance
from shapely.geometry import Point, LineString, Polygon, GeometryCollection


class OsmFile(object):
    """OSM File output"""
    def __init__(self, options=dict(), filespec=None, outdir=None):
        self.options = options
        # Read the config file to get our OSM credentials, if we have any
        # self.config = config.config(self.options)
        self.version = 3
        self.visible = 'true'
        self.osmid = -1
        # Open the OSM output file
        if filespec is None:
            if 'outdir' in self.options:
                self.file = self.options.get('outdir') + "foobar.osm"
        else:
            self.file = open(filespec, 'w')
            # self.file = open(filespec + ".osm", 'w')
        logging.info("Opened output file: " + filespec )
        #logging.error("Couldn't open %s for writing!" % filespec)

        # This is the file that contains all the filtering data
        # self.ctable = convfile(self.options.get('convfile'))
        # self.options['convfile'] = None
        # These are for importing the CO addresses
        self.full = None
        self.addr = None
        # decrement the ID
        self.start = -1

    def isclosed(self):
        return self.file.closed

    def header(self):
        if self.file is not False:
            self.file.write('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n')
            #self.file.write('<osm version="0.6" generator="gosm 0.1" timestamp="2017-03-13T21:43:02Z">\n')
            self.file.write('<osm version="0.6" generator="gosm 0.1">\n')

    def footer(self):
        #logging.debug("FIXME: %r" % self.file)
        self.file.write("</osm>\n")
        if self.file != False:
            self.file.close()

    def write(self, way=list()):
        if way is not None:
            for line in way:
                self.file.write("%s\n" % line)

    def createWay(self, way, modified=False, delete=False):
        """This creates a list with the nodes and tags of a way. Unlike
        the normal method of creating a way from a data import, this assumes
        all validation has been done, and the way is the result of an SQl
        query so doesn't need any changes."""
        attrs = dict()
        osm = list()

        # Add default attributes
        attrs['version'] = 1
        if 'osm_way_id' in way:
            attrs['id'] = int(way['osm_way_id'])
        elif 'osm_id' in way:
            attrs['id'] = int(way['osm_id'])
        else:
            attrs['id'] = self.start
            self.start -= 1

        # Create a node for each ref. Since these nodes are part of a
        # way, they have no tags. Only a POI, way or relation has tags.
        if 'wkb' not in way:
            return None
        if type(way['wkb'][0]) == LineString:
            lon = way['wkb'][0].xy[0]
            lat = way['wkb'][0].xy[1]
        elif type(way['wkb']) == GeometryCollection:
            lon,lat = way['wkb'][0].exterior.coords.xy
        else:
            logging.error("Don't know how to parse object! %r" % type(way['wkb']))
            return None

        # for x,y in way['wkb'][0].exterior.coords:
        #    print(x,y)
   
        # Create a node for each ref
        refs = list()
        for a,o in zip(lat,lon):
            notags = dict()
            notags['lat'] = a
            notags['lon'] = o
            node,ref = self.createNode(notags, modified=True)
            refs.append(ref)
            osm.append(node[0].replace(' >', ' />'))

        # Start the way
        # attrs['timestamp'] = datetime.now().strftime("%Y-%m-%dT%TZ")
        self.start -= 1
        if modified:
            line = '  <way id="%d" version="%s" action="modify" timestamp="%s">' % (attrs['id'], attrs['version'], datetime.now().strftime("%Y-%m-%dT%TZ"))
        elif delete:
            line = '  <way id="%d" version="%s" action="delete" timestamp="%s">' % (attrs['id'], attrs['version'], datetime.now().strftime("%Y-%m-%dT%TZ"))
        else:
            line = '  <way id="%d" version="%s" timestamp="%s">' % (self.start, attrs['version'], datetime.now().strftime("%Y-%m-%dT%TZ"))
            
        osm.append(line)
        for ref in refs:
            if ref != 'osm_id':
                line = '    <nd ref="%s"/>' % ref
            osm.append(line)
        # lines don't close, only polygons
        if type(way['wkb'][0]) != LineString:
            line = '    <nd ref="%s"/>' % refs[0]
            osm.append(line)

        for key, value in way.items():
            if key != "osm_way_id" and key != "osm_id" and key != "refs" and key != "cp" and key != "area" and key != 'wkb' and value is not None and value != 'None':
                line = '    <tag k="%s" v="%s"/>' % (key, value)
                osm.append(line)
        osm.append('    <tag k="fixme" v="Do not upload this without validation!"/>')
        osm.append("  </way>")

        return osm

    def createObject(self, odk):
        # odk.dump()
        alltags = list()
        nodes = list()
        attrs = dict()
        if odk.type == 'geopoint':
            node = dict()
            gps = odk.data.split(' ')
            node['lat'] = gps[0]
            node['lon'] = gps[1]
            # print(gps[0], gps[1])
            return makeNode(node, modified=True)
        elif odk.type == 'geotrace':
            linestring = odk.data.split(';')
            for x in linestring:
                gps = odk.data.split(' ')
                if len(gps) == 1:
                    break
                node = dict()
                node['lat'] = gps[0]
                node['lon'] = gps[1]
                nodes.append(node)
            # print(gps[0], gps[1])
        elif odk.type == 'string':
            tag = self.makeTag(odk.name, odk.data)
            alltags.append(tag)
        #    return self.makeWay(modified=True)

    def makeNode(self, node, modified=False):
        node.dump()
        """This creates a list with the nodes and tags of a way. Unlike
        the normal method of creating a way from a data import, this assumes
        all validation has been done, and the way is the result of an SQl
        query so doesn't need any changes."""
        # print(node)
        attrs = dict()
        osm = list()
        if modified:
            attrs['action'] = 'modify'
        self.start -= 1

        if 'osm_id' in node:
            attrs['id'] = int(node['osm_id'])
        else:
            attrs['id'] = str(self.start)
        attrs['version'] = "1"
        if 'wkb' in node:
            # it's a geometry collection object
            if type(node['wkb']) == GeometryCollection:
                if type(node['wkb'][0]) == Point:
                    attrs['lat'] = node['wkb'][0].y
                    attrs['lon'] = node['wkb'][0].x
            else:
                attrs['lat'] = node['wkb'].y
                attrs['lon'] = node['wkb'].x
        else:
            attrs['lat'] = node['lat']
            attrs['lon'] = node['lon']

        attrs['timestamp'] = datetime.now().strftime("%Y-%m-%dT%TZ")
        line = ""
        for ref, value in attrs.items():
            line += '%s=%r ' % (ref, str(value))
        osm.append("  <node %s>" % line)

        for key, value in node.items():
            if key != 'osm_id' and key != 'id' and key != 'lat' and key != 'lon' and key != 'cp' and key != 'wkb' and value != 'None' and value is not None:
                if type(value) != str:
                    line = '    <tag k="%s" v="%r"/>' % (key, value)
                else:
                    line = '    <tag k="%s" v="%s"/>' % (key, value.replace('&', 'and'))
                osm.append(line)
        if modified:
            osm.append('    <tag k="fixme" v="Do not upload this without validation!"/>')
        osm.append("  </node>")

        return osm,self.start

    def getCurrentID(self):
        return self.start

    def writeNode(self, tags=list(), attrs=dict(), modified=False):
        #        timestamp = ""  # LastUpdate
        timestamp = datetime.now().strftime("%Y-%m-%dT%TZ")
        # self.file.write("       <node id='" + str(self.osmid) + "\' visible='true'")

        if not 'osmid' in attrs:
            attrs['id'] = str(self.osmid)
            self.osmid -= 1

        if 'user' in attrs:
            try:
                x = str(attrs['user'])
            except:
                attrs['user'] = str(self.options.get('user'))
        if 'uid' in attrs:
            try:
                x = str(attrs['uid'])
            except:
                attrs['uid'] = str(self.options.get('uid'))

        if len(attrs) > 0:
            self.file.write("    <node")
            for ref,value in attrs.items():
                self.file.write(" " + ref + "=\"" + value + "\"")
            if len(tags) > 0:
                self.file.write(">\n")
            else:
                self.file.write("/>\n")

        # for i in tags:
        #     for name, value in i.items():
        #         if name == "Ignore" or value == None:
        #             continue
        #         if str(value)[0] != 'b':
        #             if value != 'None' or value != 'Ignore':
        #                 tag = self.makeTag(name, value)
        #                 for newname, newvalue in tag.items():
        #                     # if newname == 'addr:street' or newname == 'addr:full' or newname == 'name' or newname == 'alt_name':
        #                     #     newvalue = string.capwords(newvalue)
        #                     self.file.write("    <tag k=\'" + newname + "\' v=\'" + str(newvalue) + "\'/>\n")

        if len(tags) > 0:
            self.file.write("    </node>\n")

        return self.osmid

    # Here's where the fun starts. Read a field header from a file,
    # which of course are all different. Make an attempt to match these
    # random field names to standard OSM tag names. Same for the values,
    # which for OSM often have defined ranges.
    def makeTag(self, field, value):
        newval = str(value)
        #newval = html.unescape(newval)
        newval = newval.replace('&', 'and')
        newval = newval.replace('"', '')
        #newval = newval.replace('><', '')
        tag = dict()
        # logging.debug("OSM:makeTag(field=%r, value=%r)" % (field, newval))

        # try:
        #     newtag = self.ctable.match(field)
        # except Exception as inst:
        #     logging.warning("MISSING Field: %r, %r" % (field, newval))
        #     # If it's not in the conversion file, assume it maps directly
        #     # to an official OSM tag.
        #     newtag = field
        newtag = field

        #newval = self.ctable.attribute(newtag, newval)
        #logging.debug("ATTRS1: %r %r" % (newtag, newval))
        change = newval.split('=')
        if len(change) > 1:
            newtag = change[0]
            newval = change[1]

        tag[newtag] = newval
        # tag[newtag] = string.capwords(newval)

        #print("ATTRS2: %r %r" % (newtag, newval))
        return tag

    def makeWay(self, refs, tags=list(), attrs=dict(), modified=True):
        if len(refs) is 0:
            logging.error("No refs! %r" % tags)
            return

        if len(attrs) > 0:
            self.file.write("  <way")
            for ref,value in attrs.items():
                self.file.write("    " + ref + "=\"" + value + "\"")
            self.file.write(">\n")
        else:
            #logging.debug("osmfile::way(refs=%r, tags=%r)" % (refs, tags))
            #logging.debug("osmfile::way(tags=%r)" % (tags))
            self.file.write("    <way")
            timestamp = datetime.now().strftime("%Y-%m-%dT%TZ")

            if modified:
                self.file.write(" action='modified'")
            self.file.write(" version='1'")
            if 'osm_id' in attrs:
                self.file.write(" id=\'" + str(attrs['osm_id']) + "\'")
            else:
                self.file.write(" id=\'" + str(self.osmid) + "\'")
            self.file.write(" timestamp='" + timestamp + "\'>\n")
#            self.file.write(" user='" + self.options.get('user') + "' uid='" +
#                            str(self.options.get('uid')) + "'>'\n")

        # Each ref ID points to a node id. The coordinates is im the node.
        for ref in refs:
            # FIXME: Ignore any refs that point to ourself. There shouldn't be
            # any, so this is likely a bug elsewhere when parsing the geom.
            # logging.debug("osmfile::way(ref=%r, osmid=%r)" % (ref, self.osmid))
            if ref == self.osmid:
                break
            self.file.write("    <nd ref=\"" + str(ref) + "\"/>\n")

        value = ""

        for i in tags:
            for name, value in i.items():
                if name == "Ignore" or value == '':
                    continue
                if str(value)[0] != 'b':
                    self.file.write("    <tag k=\"" + name + "\" v=\"" +
                                    str(value) + "\"/>\n")

        self.file.write("  </way>\n")
        self.osmid = int(self.osmid) - 1

    def makeRelation(self, members, tags=list(), attrs=dict()):
        if len(attrs) > 0:
            self.file.write("  <relation")
            for ref,value in attrs.items():
                self.file.write(" " + ref + "=\"" + value + "\"")
            self.file.write(">\n")

        # Each ref ID points to a node id. The coordinates is im the node.
        for mattr in members:
            for ref, value in mattr.items():
                #print("FIXME: %r %r" % (ref, value))
                if ref == 'type':
                    self.file.write("    <member")
                self.file.write(" " + ref + "=\"" + value + "\"")
                if ref == 'role':
                    self.file.write("/>\n")

        value = ""

        for i in tags:
            for name, value in i.items():
                if name == "Ignore" or value == '':
                    continue
                if str(value)[0] != 'b':
                    self.file.write("    <tag k=\"" + name + "\" v=\"" + str(value) + "\"/>\n")
            
        self.file.write("  </relation>\n")

    def cleanup(self, tags):
        cache = dict()
        for tag in tags:
            for name, value in tag.items():
                try:
                    if cache[name] != value:
                        tmp = cache[name]
                        cache[name] += ';' + value
                except:
                    cache[name] = value

        tags = list()
        tags.append(cache)
        return tags
