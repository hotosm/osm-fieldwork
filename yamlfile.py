#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
#
# This file is part of odkconvert.
#
#     ODKConvert is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Underpass is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with odkconvert.  If not, see <https:#www.gnu.org/licenses/>.
#

import yaml

"""This parses a yaml file into a dictionary for easy access."""


class YamlFile(object):
    """Config file in YAML format"""
    def __init__(self, filespec=None):
        self.filespec = filespec
        self.file = open(filespec, 'rb').read()
        #print(self.file)
        self.yaml = yaml.load(self.file, Loader=yaml.Loader)

    def getValues(self, value=None):
        """Get the values for a primary key"""
        if value is not None:
            ret = dict()
            try:
                # Convert the list to a dictionary
                for entry in self.yaml[value]:
                    tmp = list(entry.keys())[0]
                    ret[tmp] = entry[tmp]
            except KeyError:
                for key in self.yaml['tags']:
                    for foo, bar in key.items():
                        if foo == value:
                            return bar
            return ret
        else:
            return None

    def getKeyword(self, value=None):
        """Get the value for a keyword"""
        for tags in self.yaml['tags']:
            for key, val in tags.items():
                if type(val) == list:
                    for item in val:
                        #print(item)
                        if item == value:
                            return key
                elif type(val) == bool:
                    if val == value:
                        # can't search for a boolean value. In that case
                        # you check the value of the keyword instead.
                        pass
                elif type(val) == dict:
                    print("DICT")
                    for item, entry in val.items():
                        print(item, entry)
        return value

    def dump(self):
        """Dump the contents of the yaml file"""
        print("YAML file: %s" % self.filespec)
        print(self.yaml)
