#!/usr/bin/python3

import os
import sys
import argparse
import geojson
import json
import flatdict

def jr2geojson(jr):
    """
    Converts a JavaRosa string of a polygon, or a list of a point, to a 
    GeoJSON geometry with coordinates and type.
    """
    coords = []
    geometry = None
    if isinstance(jr, list):
        coords = jr[0],jr[1]
        geometry = geojson.Point(coords)
    else:
        nodes = jr.split(';')
        for node in nodes:
            y = (node.strip().split(' '))[0]
            x = (node.strip().split(' '))[1]
            coords.append((float(x),float(y)))
        geometry = geojson.Polygon([coords])
    return geometry

def convertsub(sub):
    """
    Convert a dict representing a single ODK survey to a GeoJSON feature
    """
    flt = flatdict.FlatDict(sub, delimiter='-')
    props = flt
    geometry = None
    try:
        props['select_feature-xid'] = flt['select_feature-xid']
    except Exception as e:
        print('No go on the xid')
        print(e)
    try:
        if flt['select_feature-xlocation'] != None:
            geometry = jr2geojson(flt['select_feature-xlocation'])
    except Exception as e:
        print('No go on the xlocation')
        print(e)
    try:
        if('manual_geolocation-manual_geopoint-coordinates' in flt.keys()):
            if(flt['manual_geolocation-manual_geopoint-coordinates'] != None):
                geometry = jr2geojson(flt['manual_geolocation-'
                                          'manual_geopoint-'
                                          'coordinates'])                
    except Exception as e:
        print(f'\nNo go on the manual geolocation')
        print(flt['manual_geolocation-manual_geopoint-coordinates'])
        print(e)
    propsdict = dict(flt)
    feature = geojson.Feature(geometry = geometry, properties = propsdict)
    return feature
    
def main():
    """
    """
    p = argparse.ArgumentParser(
        description="Convert ODK submissions json file to GeoJson"
    )
    p.add_argument("-i", "--infile", required=True, help="The instance file(s) from ODK Collect")
    p.add_argument("-o","--outfile", default='tmp.geojson', help='The output file for JOSM')
    args = p.parse_args()

    subsfile = open(args.infile, 'r')
    subs = json.loads(subsfile.read())
    features = []
    for sub in subs:
        features.append(convertsub(sub))
    featurecollection = geojson.FeatureCollection(features)
    towrite = geojson.dumps(featurecollection)
    with open(args.outfile, 'w') as of:
        of.writelines(towrite)

if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
