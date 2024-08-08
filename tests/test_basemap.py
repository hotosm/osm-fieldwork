#!/usr/bin/python3

# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm_fieldwork.
#
#     Underpass is free software: you can redistribute it and/or modify
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
#     along with osm_fieldwork.  If not, see <https://www.gnu.org/licenses/>.
#
"""Test functionality of basemapper.py."""
import logging
import os
import shutil
from io import BytesIO
from pathlib import Path
import json

import pytest
from pmtiles.reader import MemorySource
from pmtiles.reader import Reader as PMTileReader

from osm_fieldwork.basemapper import (
    BaseMapper, create_basemap_file, BoundaryHandlerFactory,
    BytesIOBoundaryHandler, StringBoundaryHandler
)
from osm_fieldwork.sqlite import DataFile

log = logging.getLogger(__name__)

rootdir = os.path.dirname(os.path.abspath(__file__))
string_boundary = "-105.642662 39.917580 -105.631343 39.929250"
with open(Path(f"{rootdir}/testdata/Rollinsville.geojson"), "rb") as geojson_file:
    boundary = geojson_file.read()
    object_boundary = BytesIO(boundary)
outfile = f"{rootdir}/testdata/rollinsville.mbtiles"
base = "./tiles"

@pytest.fixture
def setup_boundary():
    return string_boundary, object_boundary

@pytest.mark.parametrize("boundary", [string_boundary, object_boundary])
def test_create(boundary):
    """See if the file got loaded and tiles are correct."""
    hits = 0
    basemap = BaseMapper(boundary, base, "topo")
    tiles = []
    for level in range(8, 13):
        basemap.getTiles(level)
        tiles += basemap.tiles

    assert len(tiles) > 0, "No tiles were created"

    if len(tiles) == 5:
        hits += 1

    if len(tiles) >= 3 and tiles[0].x == 52 and tiles[1].y == 193 and tiles[2].x == 211:
        hits += 1

    outf = DataFile(outfile, basemap.getFormat())
    outf.writeTiles(tiles, base)

    assert os.path.exists(outfile), "Output file was not created"
    assert hits == 2, "Hit count does not match expected value"

    os.remove(outfile)
    shutil.rmtree(base)

def test_pmtiles():
    """Test PMTile creation via helper function.

    NOTE at zoom 12-14 tiles won't easily be visible on a web map.
    This is purely for a faster test suite.
    """
     
    create_basemap_file(
        boundary="-4.730494 41.650541 -4.725634 41.652874",
        outfile=f"{rootdir}/../test.pmtiles",
        zooms="12-14",
        outdir=f"{rootdir}/../",
        source="esri",
    )
    pmtile_file = Path(f"{rootdir}/../test.pmtiles")
    assert pmtile_file.exists()  
    with open(pmtile_file, "rb") as pmtile_file:
        data = pmtile_file.read()
    pmtile = PMTileReader(MemorySource(data))
    
    data_length = pmtile.header().get("tile_data_length", 0)
    assert 2000 < data_length < 80000, "Data length out of expected range"
    assert len(pmtile.metadata().keys()) == 1
    
    metadata = pmtile.metadata()
    attribution = metadata.get("attribution")
    assert attribution == "© esri"
    
    header = pmtile.header()
    min_zoom = header.get("min_zoom")
    assert min_zoom == 12
    max_zoom = header.get("max_zoom")
    assert max_zoom == 14



class TestBoundaryHandlerFactory:
    
    def test_get_bounding_box(self):
        boundary = "10,20,30,40"
        factory = BoundaryHandlerFactory(boundary)
        assert factory.get_bounding_box() == (10, 20, 30, 40)

class TestBytesIOBoundaryHandler:
    
    def setup_method(self):
        geojson_data = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-73.9876, 40.7661], [-73.9857, 40.7661], [-73.9857, 40.7641], [-73.9876, 40.7641], [-73.9876, 40.7661]]]
                }
            }]
        }
        self.boundary = BytesIO(json.dumps(geojson_data).encode('utf-8'))
        self.handler = BytesIOBoundaryHandler(self.boundary)
    
    def test_make_bbox(self):
        valid_geojson_data = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-73.9876, 40.7661], [-73.9857, 40.7661], [-73.9857, 40.7641], [-73.9876, 40.7641], [-73.9876, 40.7661]]]
                }
            }]
        }
        self.boundary = BytesIO(json.dumps(valid_geojson_data).encode('utf-8'))
        handler = BytesIOBoundaryHandler(self.boundary)
        bbox = handler.make_bbox()
        assert bbox == (-73.9876, 40.7641, -73.9857, 40.7661)
        
class TestStringBoundaryHandler:
    
    def test_make_bbox(self):
        handler = StringBoundaryHandler("10,20,30,40")
        bbox = handler.make_bbox()
        assert bbox == (10, 20, 30, 40)

    def test_make_bbox_invalid(self):
        handler = StringBoundaryHandler("10,20,30")
        with pytest.raises(ValueError):
            handler.make_bbox()

    def test_make_bbox_empty(self):
        handler = StringBoundaryHandler("")
        with pytest.raises(ValueError):
            handler.make_bbox()

if __name__ == "__main__":
    pytest.main()
