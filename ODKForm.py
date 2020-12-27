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


class ODKForm(object):
    """Support for parsing an XLS Form"""
    def __init__(self):
        self.fields = dict()
        self.nodesets = dict()

    def parse(self, file):
        print("Parsing form %r" % file.name)
        doc = etree.parse(file)

        head = list()
        body = dict()
        base = ""
        title = ""
        for docit in doc.getiterator():
            if base == "":
                base = docit.base
                # print("BAR: %r" % (docit.tag))
            if docit.prefix == 'h':
                index = docit.tag.find('}') + 1
                if docit.tag[index:] == 'title':
                    title = docit.text
                    # Process the header
                elif docit.tag[index:] == 'head':
                    for elit in docit.getiterator():
                        try:
                            index = elit.tag.find('}') + 1
                        except:
                            continue
                        if elit.tag[index:] == 'text':
                            # print("HEADY: %r" % elit)
                            if elit.attrib != "":
                                attr = dict(elit.attrib)
                                # print("HEAD: %r" % (attr['id']))
                                id = attr['id']
                                head.append(id)
                                index = id.find(':')
                                field = id[6:index]
                                index = index + 1
                                opt = id[index:]
                                print("FIELD %r %r" % (field, opt))
                                if opt == 'hint':
                                    continue
                                elif opt == 'label':
                                    item = field.split("/")
                                    if len(item) > 1:
                                        self.fields[item[0]] = item[1]
                                if opt[0:6] == 'option':
                                    text = str(etree.tostring(elit[0]))
                                    start = text.find('>') + 1
                                    end = text.find('<',start)
                                    value = text[start:end]
                                    print('OPTION %r' % value)
                                    item = (field + ':' + opt, value)
                                    # fields.append(item)
                                   # import pdb; pdb.set_trace()

                    #print("FIELDS1: %r" % fields)
                # Process the body
                elif docit.tag[index:] == 'body':
                    for elit in docit.getiterator():
                        # print("BODY TEXT: %r %r" % (elit.tag, elit.text))
                        # mport epdb; epdb.st()
                        for ref,datatype in elit.items():
                            dtype = datatype[6:]
                            # print("\tFOOBAR: %r , %r" % (ref, dtype))
                            options = list()
                            for select in elit.getiterator():
                                if type(select.text) == str:
                                    if select.text[0] != '\n':
                                        # print("\tSELECT BODY: %r" % (select.text))
                                        options.append(select.text)
                                        #import pdb; pdb.set_trace()
                                #value = l
                                #body[dtype] = options
                            if len(options) > 0:
                                body[dtype] = options

            try:
                index = docit.tag.find('}') + 1
            except:
                continue
            if docit.tag[index:] == 'bind':
                # print("DOCIT.TAG: %r" % docit.tag)
                try:
                    # print("DOCIT.ATTRIB: %r" % docit.attrib)
                    btype = docit.attrib['type']
                    bname = docit.attrib['nodeset'].replace("/data/","")
                except:
                    btype = "unknown"
                    bname = "unknown"
                self.nodesets[bname] = btype

    def getNodeType(self, name):
        if name in self.nodesets:
            return self.nodesets[name]
        else:
            return None

    def dump(self):
        print("Dumping Nodesets:")
        for key,value in self.nodesets.items():
            print("\tType of \'%s\' is \'%s\'" % (key, value))
        print("Dumping Data Fields:")
        for key,value in self.fields.items():
            print("\tField of \'%s\' is \'%s\'" % (key, value))


#
# End of Class definitions
#

file = open("/home/rob/projects/gnu/gosm.git/ODK/IcePark.xml")
odkform = ODKForm()
xmlfile = odkform.parse(file)
odkform.dump()
# print("HEAD: %r" % xmlfile['head'])
# print("BODY: %r" % xmlfile['body'])
# print("BASE: %r" % xmlfile['base'])
# print("FIELDS: %r" % xmlfile['fields'])
# print("NODESETS: %r" % xmlfile['nodesets'])
# print(odkform.getNodeType('name'))
