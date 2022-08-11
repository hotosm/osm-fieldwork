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

from yamlfile import YamlFile
import logging


class Convert(YamlFile):
    """A class to apply a YAML config file and convert ODK to OSM"""
    def __init__(self, xform=None):
        if xform is None:
            xform = "xforms.yaml"
        self.yaml = YamlFile(xform)
        # self.yaml.dump()

    def escape(self, value):
        """Escape characters like embedded quotes in text fields"""
        tmp = value.replace(" ", "_")
        return tmp.replace("'", "&apos;")

    def getKeyword(self, value):
        """Get the value for a keyword from the yaml file"""
        key = self.yaml.getValues(value)
        if type(key) == bool:
            return value
        if len(key) == 0:
            key = self.yaml.getKeyword(value)
        return key

    def convertList(self, values=list()):
        """Convert a python list of tags"""
        features = list()
        entry = dict()
        for value in values:
            entry[self.yaml.getKeyword(value)] = value
            features.append(entry)
        return features

    def convertTag(self, tag, value):
        """Convert a single tag"""
        values = self.yaml.getValues("convert")
        if tag in values:
            val = values[tag]
            if type(val) == str:
                logging.debug("\tTag %s converted to %s" % (tag, val))
            else:
                for item in val:
                    key = list(item.keys())[0]
                    if key == value:
                        tmp = item[key].split("=")
                        return tmp[0], tmp[1]
            return val, value
        return tag, value
