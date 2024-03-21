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
#     along with osm_fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Test functionalty of basemapper.py."""

import pytest
import logging
import os
import shutil

from osm_fieldwork.basemapper import BaseMapper
from osm_fieldwork.basemapper import create_basemap_file
from osm_fieldwork.sqlite import DataFile

log = logging.getLogger(__name__)

rootdir = os.path.dirname(os.path.abspath(__file__))
boundary = f"{rootdir}/testdata/Rollinsville.geojson"
outfile = f"{rootdir}/testdata/rollinsville.mbtiles"
tms_url = "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
zooms = "10-12"
base = "./tiles"


def test_create_basemap_valid_parameters():
    """Test the creation of a basemap with valid parameters.

    This test function verifies that a basemap can be created 
    successfully with valid parameters.
    It calls the create_basemap_file function with valid boundary, 
    output file, zoom levels, and source information. It then checks 
    whether the output file exists after the basemap creation.
    """
    create_basemap_file(
        boundary=boundary,
        outfile=outfile,
        zooms=zooms,
        outdir=None,
        source="esri",
    )
    assert os.path.exists(outfile)


def test_create_basemap_invalid_parameters():
    """Test the creation of a basemap with invalid parameters.

    This test function ensures that creating a basemap with 
    invalid parameters raises a ValueError.
    It calls the create_basemap_file function with invalid 
    boundary and output file valuesand checks whether a ValueError 
    is raised.
    """
    with pytest.raises(ValueError):
        create_basemap_file(
            boundary=None,
            outfile=None,
            zooms=zooms,
            outdir=None,
            source="esri",
        )


def test_custom_tms():
    """Test custom tile mapping service.

    This test function checks the functionality 
    of custom tile mapping service (TMS).
    It creates an instance of BaseMapper and 
    sets a custom TMS URL. Then it verifies
    that the custom TMS URL is correctly set in the sources dictionary.
    """
    basemap = BaseMapper(boundary, base=None, source="esri", xy=False)
    tms_url = "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
    basemap.customTMS(tms_url)
    expected_url = "https://a.tile.openstreetmap.org/%s"
    assert basemap.sources["custom"]["url"] == expected_url


def test_pmtiles_generation():
    """Test the generation of pmtiles.

    This test function validates the generation of 
    pmtiles (Portable Map Tiles).
    It calls the create_basemap_file function to 
    generate pmtiles with specified boundary,
    output file, zoom levels, and source information. 
    Then it checks whether the output file exists.
    """
    create_basemap_file(
        boundary=boundary,
        outfile=outfile,
        zooms=zooms,
        outdir=None,
        source="esri",
    )
    assert os.path.exists(outfile)


# def test_boundary_parsing():
#     expected_bbox = (-105.605833, 39.920833, -105.585833, 39.940833)
#     basemap = BaseMapper(boundary, base=None, source="esri", xy=False)
#     assert basemap.bbox == expected_bbox

# def test_tile_id_generation():
#     from osm_fieldwork.basemapper import tileid_from_y_tile
#     tile_path = "esritiles/12/1525/1994.jpg"
#     tile_id = tileid_from_y_tile(tile_path)
#     assert tile_id == (12, 1525, 1994)


def test_create():
    """See if the file got loaded.

    This test function ensures that a file is 
    successfully loaded and processed.
    It creates an instance of BaseMapper, 
    retrieves tiles at specified zoom levels,
    and writes the tiles to an output file.
    """
    hits = 0
    basemap = BaseMapper(boundary, base, "topo", False)
    tiles = list()
    for level in [8, 9, 10, 11, 12]:
        basemap.getTiles(level)
        tiles += basemap.tiles

    if len(tiles) == 5:
        hits += 1

    if tiles[0].x == 52 and tiles[1].y == 193 and tiles[2].x == 211:
        hits += 1

    outf = DataFile(outfile, basemap.getFormat())
    outf.writeTiles(tiles, base)

    os.remove(outfile)
    shutil.rmtree(base)

    assert hits == 2


if __name__ == "__main__":
    test_create()
    pytest.main()
