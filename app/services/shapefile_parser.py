"""Shapefile parser for compressed (.zip) ESRI Shapefile archives.

Handles archives containing .shp, .shx, .dbf, and .prj files.
Extracts geometries into Shapely objects, reads attribute records,
and parses projection metadata from .prj files.
"""

import io
import os
import zipfile
from typing import Any, Dict, List, Optional, Tuple
import pyproj
import shapefile
import shapely
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid
from app.config import settings


class ShapefileParser:
    """Parses zipped ESRI Shapefiles into Shapely geometries and attribute records."""

    @classmethod
    def parse_zip_bytes(
        cls, zip_content: bytes
    ) -> Tuple[List[Dict[str, Any]], pyproj.CRS]:
        """
        Parses a .zip archive containing shapefile components (.shp, .shx, .dbf, .prj).

        Returns:
            Tuple of (features_list, pyproj.CRS)
        """
        try:
            zf = zipfile.ZipFile(io.BytesIO(zip_content))
        except zipfile.BadZipFile:
            raise ValueError("The uploaded file is not a valid or readable ZIP archive.")

        # Identify files in zip (case-insensitive)
        file_map: Dict[str, str] = {}
        for name in zf.namelist():
            # Skip MacOS hidden folders like __MACOSX/
            if name.startswith("__MACOSX") or os.path.basename(name).startswith("."):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext in (".shp", ".shx", ".dbf", ".prj"):
                base_stem = os.path.splitext(os.path.basename(name))[0].lower()
                file_map[f"{base_stem}{ext}"] = name

        # Find .shp file
        shp_keys = [k for k in file_map if k.endswith(".shp")]
        if not shp_keys:
            raise ValueError(
                "No .shp file found in ZIP archive. Ensure your zip contains an ESRI shapefile (.shp, .dbf, .prj)."
            )

        # Select primary shapefile stem
        primary_key = shp_keys[0]
        base_stem = primary_key[:-4]

        shp_path = file_map.get(f"{base_stem}.shp")
        dbf_path = file_map.get(f"{base_stem}.dbf")
        shx_path = file_map.get(f"{base_stem}.shx")
        prj_path = file_map.get(f"{base_stem}.prj")

        if not dbf_path:
            raise ValueError("Shapefile archive is incomplete: missing required .dbf attribute file.")

        # Read CRS from .prj if present
        source_crs = pyproj.CRS.from_epsg(4326)
        if prj_path:
            try:
                prj_text = zf.read(prj_path).decode("utf-8", errors="ignore").strip()
                if prj_text:
                    source_crs = pyproj.CRS.from_user_input(prj_text)
            except Exception:
                # Fallback to default
                source_crs = pyproj.CRS.from_epsg(4326)

        # Open shapefile in memory
        shp_file = io.BytesIO(zf.read(shp_path))
        dbf_file = io.BytesIO(zf.read(dbf_path))
        shx_file = io.BytesIO(zf.read(shx_path)) if shx_path else None

        try:
            reader = shapefile.Reader(shp=shp_file, dbf=dbf_file, shx=shx_file)
        except Exception as e:
            raise ValueError(f"Failed to read Shapefile: {str(e)}")

        features: List[Dict[str, Any]] = []

        for idx, shape_rec in enumerate(reader.shapeRecords()):
            # Parse record attributes
            try:
                props = shape_rec.record.as_dict()
            except Exception:
                props = {}

            # Parse shape geometry via geo_interface
            geom_dict = shape_rec.shape.__geo_interface__
            try:
                geom: BaseGeometry = shape(geom_dict)
                if not geom.is_valid:
                    geom = make_valid(geom)
            except Exception as e:
                # Handle corrupted geometry gracefully
                continue

            features.append({
                "id": props.get("id") or props.get("ID") or f"feature_{idx}",
                "geometry": geom,
                "properties": props,
            })

        return features, source_crs
