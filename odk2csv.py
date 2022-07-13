#!/usr/bin/python3

#
#   Copyright (C) 2020, 2021, 2022 Humanitarian OpenstreetMap Team
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
import argparse
import xmltodict
import os
import sys
import re
from collections import OrderedDict
import csv


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert ODK XML instance file to CSV format')
    parser.add_argument("-v", "--verbose", nargs="?",const="0", help="verbose output")
    parser.add_argument("-i","--instance", default="Test.xml", help='The instance file from ODK Collect')
    #parser.add_argument("-o","--outfile", default='tmp.csv', help='The output file for JOSM')
    args = parser.parse_args()

    # if verbose, dump to the termina
    if not args.verbose:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)

    with open(args.instance, 'rb') as file:
        # Instances are small, read the whole file        
        xml = file.read(os.path.getsize(args.instance))
        doc = xmltodict.parse(xml)
        fields = list()
        tags = dict()
        # import epdb; epdb.st()
        data = doc['data']
        for i, j in data.items():
            if j is None:
                continue
            print(i, j)
            pat = re.compile("[0-9.]* [0-9.-]* [0-9.]* [0-9.]*")
            if pat.match(str(j)):
                fields.append("lat")
                gps = j.split(' ')
                tags["lat"] = gps[0]
                fields.append("lon")
                tags["lon"] = gps[1]
                continue
            if type(j) == OrderedDict:
                for ii, jj in j.items():
                    if jj is None:
                        continue
                    if ii[0:1] != "@":
                        fields.append(ii)
                    if type(jj) == OrderedDict:
                        for iii, jjj in jj.items():
                            if jjj is not None:
                                fields.append(iii)
                                tags[iii] = jjj
                                # print(iii, jjj)
                    else:
                        # print(ii, jj)
                        tags[ii] = jj
            else:
                if i[0:1] != "@":
                    fields.append(i)
                    tags[i] = j

    outfile = args.instance.replace(".xml", ".csv")
    with open(outfile, 'w', newline='') as csvfile:
        csv = csv.DictWriter(csvfile, dialect='excel',fieldnames=fields)
        csv.writeheader()
        csv.writerow(tags)

