"""CRS Transformation Engine for Geospatial Geometry Reprojection.

Addresses Requirement 5:
- Detects geographic coordinate reference systems (e.g., EPSG:4326 in degrees).
- Prevents naive degree-based calculations.
- Dynamically derives the optimal projected CRS (Local UTM Zone or Equal-Area).
- Transforms geometries using high-performance pyproj and shapely 2.0 vector operations.
"""

from typing import Optional, Tuple
import numpy as np
import pyproj
import shapely
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid


class CRSTransformer:
    """Manages CRS identification, optimal projection selection, and coordinate reprojection."""

    @staticmethod
    def parse_crs(crs_input: Optional[str]) -> pyproj.CRS:
        """
        Parse and normalize a CRS representation (EPSG code, WKT string, or proj string).
        Defaults to EPSG:4326 if None or unparseable.
        """
        if not crs_input or str(crs_input).strip() == "":
            return pyproj.CRS.from_epsg(4326)

        try:
            return pyproj.CRS.from_user_input(crs_input)
        except Exception:
            # Fallback to EPSG:4326
            return pyproj.CRS.from_epsg(4326)

    @classmethod
    def get_optimal_projected_crs(
        cls,
        geometry: BaseGeometry,
        source_crs: pyproj.CRS,
    ) -> pyproj.CRS:
        """
        Determine the optimal projected CRS for accurate area and distance calculations.

        Strategy:
        1. If source CRS is already a local projected system (e.g., UTM) with meter units,
           we preserve it unless it is Web Mercator (EPSG:3857), which distorts area significantly.
        2. If source CRS is geographic (degrees like EPSG:4326):
           - Compute geometry centroid (lon, lat).
           - If span is wide (>6 degrees longitude), use World Cylindrical Equal Area (EPSG:6933).
           - Otherwise, dynamically derive the local Universal Transverse Mercator (UTM) zone
             (EPSG:32601-32660 for North, EPSG:32701-32760 for South).
        """
        # If source is already projected and NOT EPSG:3857 (Web Mercator has high areal distortion)
        if source_crs.is_projected:
            epsg = source_crs.to_epsg()
            if epsg not in (3857, 900913):
                # Verify linear units are meters
                axis_units = [axis.unit_name for axis in source_crs.axis_info]
                if any("metre" in u.lower() or "meter" in u.lower() for u in axis_units):
                    return source_crs

        # For geographic coordinates (or reprojecting from EPSG:3857):
        # First ensure we have centroid in WGS84 coordinates (lon, lat)
        if source_crs.is_projected:
            to_wgs84 = pyproj.Transformer.from_crs(source_crs, pyproj.CRS.from_epsg(4326), always_xy=True)
            minx, miny, maxx, maxy = geometry.bounds
            center_x, center_y = (minx + maxx) / 2.0, (miny + maxy) / 2.0
            lon, lat = to_wgs84.transform(center_x, center_y)
            lon_span = abs(maxx - minx)  # Approximate
        else:
            minx, miny, maxx, maxy = geometry.bounds
            lon, lat = geometry.centroid.x, geometry.centroid.y
            lon_span = abs(maxx - minx)

        # Ensure lon is in [-180, 180] and lat in [-90, 90]
        lon = max(-180.0, min(180.0, lon))
        lat = max(-89.9, min(89.9, lat))

        # Wide regional span spanning across multiple UTM zones (>6 degrees longitude):
        # Use EPSG:6933 (World Cylindrical Equal Area) for accurate area measurements
        if lon_span > 6.0:
            return pyproj.CRS.from_epsg(6933)

        # Standard Local UTM Zone calculation:
        zone_number = int((lon + 180.0) / 6.0) + 1
        zone_number = max(1, min(60, zone_number))

        if lat >= 0.0:
            target_epsg = 32600 + zone_number  # WGS 84 / UTM zone N
        else:
            target_epsg = 32700 + zone_number  # WGS 84 / UTM zone S

        return pyproj.CRS.from_epsg(target_epsg)

    @classmethod
    def reproject_geometry(
        cls,
        geometry: BaseGeometry,
        source_crs: pyproj.CRS,
        target_crs: Optional[pyproj.CRS] = None,
    ) -> Tuple[BaseGeometry, str]:
        """
        Reproject a Shapely geometry into the target projected coordinate system.

        Returns:
            Tuple of (projected_geometry, target_crs_identifier)
        """
        if geometry.is_empty:
            return geometry, source_crs.to_string()

        # If geometry is invalid, repair it first
        if not geometry.is_valid:
            geometry = make_valid(geometry)

        # Determine target CRS if not explicitly provided
        if target_crs is None:
            target_crs = cls.get_optimal_projected_crs(geometry, source_crs)

        # If source and target are the same, return geometry directly
        if source_crs == target_crs:
            crs_id = f"EPSG:{target_crs.to_epsg()}" if target_crs.to_epsg() else target_crs.to_string()
            return geometry, crs_id

        # Setup vector transformer
        transformer = pyproj.Transformer.from_crs(source_crs, target_crs, always_xy=True)

        def _reproject_coords(coords: np.ndarray) -> np.ndarray:
            x, y = transformer.transform(coords[:, 0], coords[:, 1])
            if coords.shape[1] > 2:
                # Retain Z / elevation coordinates if present
                return np.column_stack((x, y, coords[:, 2:]))
            return np.column_stack((x, y))

        projected = shapely.transform(geometry, _reproject_coords)

        # Ensure projected geometry is topologically valid
        if not projected.is_valid:
            projected = make_valid(projected)

        target_str = f"EPSG:{target_crs.to_epsg()}" if target_crs.to_epsg() else target_crs.to_string()
        return projected, target_str
