#!/usr/bin/python3

#
#   Copyright (C) 2020, Humanitarian OpenstreetMap Team
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

# The ElementTree class has these fields:
# .attrib       - A dictionary containing the element's
#                 attributes. The keys are the attribute names, and
#                 each corresponding value is the attribute's value.
# .base         - The base URI from an xml:base attribute that this
#                 element contains or inherits, if any; None
#                 otherwise.
# .prefix       - The namespace prefix of this element, if any, otherwise None.
# .sourceline   - The line number of this element when parsed, if
#                 known, otherwise None.
# .tag          - The element's name.
# .tail         - The text following this element's closing tag, up to
#                 the start tag of the next sibling element. If there
#                 was no text there, this attribute will have the
#                 value None.
# .text         - The text inside the element, up to the start tag of
#                 the first child element. If there was no text there,
#                 this attribute will have the value None.

import os
from lxml import etree
import logging
from lxml.etree import tostring
import argparse
import xmltodict


class ODKForm(object):
    """Support for parsing an XLS Form"""
    def __init__(self):
        self.fields = dict()
        self.nodesets = dict()
        self.groups = dict()

    def parse(self, inform):
        print("Parsing form %s" % inform)

        infile = open(inform)
        data = infile.read()
        html = xmltodict.parse(data)
        for key, value in html['h:html'].items():
            if key == "h:head":
                for node in value['model']['bind']:
                    #print("\nUUU %r" % node)
                    key = node['@nodeset']
                    key = key.replace("/data/", "")
                    self.nodesets[key] = node['@type']
        print(self.nodesets)

        for key, value in html['h:html']['h:body'].items():
            for subval in value:
                if subval['@appearance'] == "field-list":
                    group = subval['@ref']
                    group = group.replace("/data/", "")
                    # print("\nXXX %r, %r" % (group, subval))
                    # non selection fields like text or range use the input keyword
                    entry = dict()
                    if 'input' in subval:
                        for val in subval['input']:
                            tmp = val['@ref']
                            tmp = tmp.replace("/data/" + group + "/", "")
                            entry[tmp] = ""
                            self.groups[group] = entry

                    # selection fields like select_one or select__multiple can havew multiple entries
                    keywords = ("select", "select1", "select2", "select3", "select4")
                    for selection in keywords:
                        if selection in subval:
                            entries = list()
                            select = subval[selection]['@ref']
                            select = select.replace("/data/" + group + "/", "")
                            for item in subval[selection]['item']:
                                # print("\nYYY %r, %r" % (select, item['value']))
                                entries.append(item['value'])
                                entry[select] = entries
                                self.groups[group] = entry
                            entry[select] = entries

        print(self.groups)

    def getNodeType(self, name):
        if name in self.nodesets:
            return self.nodesets[name]
        else:
            return None

    def dump(self):
        print("Dumping Nodesets:")
        for key, value in self.nodesets.items():
            print("\tType of \'%s\' is \'%s\'" % (key, value))
        print("Dumping Data Fields:")
        for key, value in self.fields.items():
            print("\tField of \'%s\' is \'%s\'" % (key, value))


#
# End of Class definitions
#

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='convert ODK CSV to OSM')
    parser.add_argument("--infile", required=True, help='The input file from ODK Central')
    parser.add_argument("--outfile", default='tmp.osm', help='The output file for JOSM')
    args = parser.parse_args()

    odkform = ODKForm()
    odkform.parse(args.infile)
