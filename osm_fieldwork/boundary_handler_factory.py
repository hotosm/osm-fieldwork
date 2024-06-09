from typing import Union
from io import BytesIO
from .boundary_handlers import BoundingBox, BytesIOBoundaryHandler, StringBoundaryHandler

"""
Boundary Handler Factory
This module provides a factory class for creating boundary handlers based on the type of input boundary provided.
It supports boundary inputs represented either as GeoJSON files wrapped in BytesIO, or BBOX strings.
Classes:
- BoundaryHandlerFactory: Factory class for creating boundary handlers.
"""

class BoundaryHandlerFactory:
    def __init__(self, boundary: Union[str, BytesIO]):
        if isinstance(boundary, BytesIO):
            self.handler = BytesIOBoundaryHandler(boundary)
        elif isinstance(boundary, str):
            self.handler = StringBoundaryHandler(boundary)
        else:
            raise ValueError("Unsupported type for boundary parameter.")

        self.boundary_box = self.handler.make_bbox()

    def get_bounding_box(self) -> BoundingBox:
        return self.boundary_box