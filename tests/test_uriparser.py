#!/usr/bin/python3

# Copyright (c) 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm_fieldwork.
#
#     This is free software: you can redistribute it and/or modify
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
#     along with osm_fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

import argparse
import os
import sys
from osm_fieldwork.make_data_extract import uriParser

parser = argparse.ArgumentParser(
    description="Test odk_merge"
)
parser.add_argument("--infile", help="The input file")
args = parser.parse_args()

out = None
def test_dbname_only():
    dbname = "testdb"
    db = uriParser(dbname)
    # print(db['dbname'] == dbname)
    assert(db['dbname'] == dbname)

def test_dbname():
    passes = 0
    db = uriParser("fmtm:XxXx@localhost/underpass")
    if db['dbname'] == 'underpass':
        passes += 1
    # print(db)
    db = uriParser("fmtm:XxXx/underpass")
    if db['dbname'] == 'underpass':
        passes += 1
    # print(db)
    db = uriParser("fmtm:XxXx@localhost:5433/underpass")
    if db['dbname'] == 'underpass':
        passes += 1
    #print(db)
    # print(passes == 3)
    assert(passes == 3)
    
def test_host():
    db = uriParser("fmtm@localhost")
    dbhost = db['dbhost']
    db2 = uriParser("fmtm@hostlocal")
    db2host = db2['dbhost']
    # print(dbhost == 'localhost' and db2host == 'hostlocal')
    assert(dbhost == 'localhost' and db2host == 'hostlocal')

def test_user():
    db = uriParser("fmtm@localhost")
    dbuser = db['dbuser']
    dbpass = db['dbpass']
    # print(dbuser == 'fmtm', dbpass is None)
    assert(dbuser == 'fmtm' and dbpass is None)

def test_password():
    db = uriParser("fmtm:XxXx@localhost")
    dbuser = db['dbuser']
    dbpass = db['dbpass']
    # print(dbuser == 'fmtm', dbpass == 'XxXx')
    assert(dbuser == 'fmtm' and dbpass == 'XxXx')

def test_port():
    db2 = uriParser("fmtm:XxXx@localhost:5433")
    # print(db2)
    db3 = uriParser("fmtm:XxXx@hostlocal:5433/fmtmdb")
    # print(db3)
    # print(db2['dbport'] == '5433' and db3['dbport'] == '5433')
    assert(db2['dbport'] == '5433' and db3['dbport'] == '5433')

if __name__ == "__main__":
    # print("--- test_dbname_only() ---")
    test_dbname_only()
    # print("--- test_dbname() ---")
    test_dbname()
    # print("--- test_host() ---")
    test_host()
    # print("--- test_user() ---")
    test_user()
    # print("--- test_password() ---")
    test_password()
    # print("--- test_port() ---")
    test_port()
    # print("--- done ---")
