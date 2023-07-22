#!/usr/bin/python3

import re
import sys
from sys import argv
from osm_fieldwork.json2osm import main
# import osm_fieldwork.json2osm
import osm_fieldwork.odk_merge


if __name__ == '__main__':
    app = argv[1]
    print(app)
    argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', argv[1])
    # if app == 'merge':
    #     sys.exit(osm_fieldwork.odk_merge.main())
    # elif app == 'json':
    #     sys.exit(osm_fieldwork.json2osm.main())

