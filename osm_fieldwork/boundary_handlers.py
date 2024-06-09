from typing import Union, Tuple
import logging
from io import BytesIO
import geojson
from shapely.geometry import shape
from shapely.ops import unary_union

log = logging.getLogger(__name__)

BoundingBox = Tuple[float, float, float, float]

"""
Boundary Handlers for Bounding Box (BBOX) Extraction
This module provides classes to extract Bounding Box (BBOX) from various boundary representations,
including GeoJSON files wrapped in BytesIO object, and BBOX strings.
Classes:
- BytesIOBoundaryHandler: Extracts BBOX from GeoJSON data stored in a BytesIO object.
- StringBoundaryHandler: Extracts BBOX from string representation.
"""
class BoundaryHandler:
    def make_bbox(self) -> BoundingBox:
        pass

class BytesIOBoundaryHandler(BoundaryHandler):
    def __init__(self, boundary: BytesIO):
        self.boundary = boundary

    def make_bbox(self) -> BoundingBox:
        log.debug(f"Reading geojson BytesIO : {self.boundary}")
        # Rewind the BytesIO object to the beginning before passing it to geojson.load()
        self.boundary.seek(0)
        with self.boundary as buffer:
            poly = geojson.load(buffer)

        if "features" in poly:
            geometry = shape(poly["features"][0]["geometry"])
        elif "geometry" in poly:
            geometry = shape(poly["geometry"])
        else:
            geometry = shape(poly)

        if isinstance(geometry, list):
            # Multiple geometries
            log.debug("Creating union of multiple bbox geoms")
            geometry = unary_union(geometry)

        if geometry.is_empty:
            msg = f"No bbox extracted from {geometry}"
            log.error(msg)
            raise ValueError(msg) from None

        bbox = geometry.bounds
        # left, bottom, right, top
        # minX, minY, maxX, maxY
        return bbox

class StringBoundaryHandler(BoundaryHandler):
    def __init__(self, boundary: str):
        self.boundary = boundary

    def make_bbox(self) -> BoundingBox:
        try:
            if "," in self.boundary:
                bbox_parts = self.boundary.split(",")
            else:
                bbox_parts = self.boundary.split(" ")
            bbox = tuple(float(x) for x in bbox_parts)
            if len(bbox) == 4:
                # BBOX valid
                return bbox
            else:
                msg = f"BBOX string malformed: {bbox}"
                log.error(msg)
                raise ValueError(msg) from None
        except Exception as e:
            log.error(e)
            msg = f"Failed to parse BBOX string: {self.boundary}"
            log.error(msg)
            raise ValueError(msg) from None