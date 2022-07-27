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


class Convert(YamlFile):
    """A class to apply a YAML config file and convert ODK to OSM"""
    def __init__(self, xform=None):
        if xform is None:
            xform = "xforms.yaml"
        self.yaml = YamlFile(xform)
        # self.yaml.dump()

    def escape(self, value):
        tmp = value.replace(" ", "_")
        return tmp.replace("'", "&apos;")

    def getKeyword(self, value):
        key = self.yaml.getValues(value)
        if type(key) == bool:
            return value
        if len(key) == 0:
            key = self.yaml.getKeyword(value)
        return key

    def convertList(self, values=list()):
        features = list()
        entry = dict()
        for value in values:
            entry[self.yaml.getKeyword(value)] = value
            features.append(entry)
        return features

    def convertTag(self, tag):
        for mod in self.yaml.getValues("convert"):
            if tag in mod:
                return mod[tag]
        return tag
