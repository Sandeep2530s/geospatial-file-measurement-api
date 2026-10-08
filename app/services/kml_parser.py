"""KML (Keyhole Markup Language) file parser.

Extracts Placemarks, geometries (Polygon, LineString, Point, MultiGeometry),
and attributes (name, description, ExtendedData) safely using defusedxml.
Per OGC KML 2.2 specification, coordinates are geographic WGS84 (EPSG:4326).
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import defusedxml.ElementTree as ET
import pyproj
from shapely.geometry import (
    Polygon,
    LineString,
    Point,
    MultiPolygon,
    MultiLineString,
    MultiPoint,
    GeometryCollection,
)
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid


class KMLParser:
    """Parses KML 2.2 files into Shapely geometries and attribute dictionaries."""

    DEFAULT_CRS = "EPSG:4326"

    @classmethod
    def _parse_coordinates(cls, coord_text: str) -> List[Tuple[float, ...]]:
        """Parses KML coordinate text: 'lon,lat,alt lon,lat,alt'."""
        coords: List[Tuple[float, ...]] = []
        if not coord_text:
            return coords

        for token in coord_text.strip().split():
            parts = token.split(",")
            if len(parts) >= 2:
                try:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    if len(parts) >= 3 and parts[2].strip():
                        alt = float(parts[2])
                        coords.append((lon, lat, alt))
                    else:
                        coords.append((lon, lat))
                except ValueError:
                    continue
        return coords

    @classmethod
    def _parse_geometry(cls, elem: Any) -> Optional[BaseGeometry]:
        """Recursively parses a KML geometry XML element into a Shapely geometry."""
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        if tag == "Polygon":
            outer_elem = (
                elem.find(".//{http://www.opengis.net/kml/2.2}outerBoundaryIs//{http://www.opengis.net/kml/2.2}coordinates")
                if elem.find(".//{http://www.opengis.net/kml/2.2}outerBoundaryIs//{http://www.opengis.net/kml/2.2}coordinates") is not None
                else elem.find(".//{*}outerBoundaryIs//{*}coordinates")
            )
            if outer_elem is None or not outer_elem.text:
                return None

            outer_coords = cls._parse_coordinates(outer_elem.text)
            if len(outer_coords) < 3:
                return None

            # Parse optional inner rings (holes)
            inner_rings = []
            inner_elems = (
                elem.findall(".//{http://www.opengis.net/kml/2.2}innerBoundaryIs//{http://www.opengis.net/kml/2.2}coordinates")
                or elem.findall(".//{*}innerBoundaryIs//{*}coordinates")
            )
            for in_elem in inner_elems:
                if in_elem.text:
                    in_coords = cls._parse_coordinates(in_elem.text)
                    if len(in_coords) >= 3:
                        inner_rings.append(in_coords)

            poly = Polygon(shell=outer_coords, holes=inner_rings)
            return make_valid(poly) if not poly.is_valid else poly

        elif tag == "LineString":
            coords_elem = (
                elem.find(".//{http://www.opengis.net/kml/2.2}coordinates")
                if elem.find(".//{http://www.opengis.net/kml/2.2}coordinates") is not None
                else elem.find(".//{*}coordinates")
            )
            if coords_elem is not None and coords_elem.text:
                coords = cls._parse_coordinates(coords_elem.text)
                if len(coords) >= 2:
                    return LineString(coords)
            return None

        elif tag == "Point":
            coords_elem = (
                elem.find(".//{http://www.opengis.net/kml/2.2}coordinates")
                if elem.find(".//{http://www.opengis.net/kml/2.2}coordinates") is not None
                else elem.find(".//{*}coordinates")
            )
            if coords_elem is not None and coords_elem.text:
                coords = cls._parse_coordinates(coords_elem.text)
                if coords:
                    return Point(coords[0])
            return None

        elif tag == "MultiGeometry":
            sub_geoms: List[BaseGeometry] = []
            for child in elem:
                sub_g = cls._parse_geometry(child)
                if sub_g is not None:
                    sub_geoms.append(sub_g)
            if not sub_geoms:
                return None

            # Group homogeneous geometries if possible
            if all(isinstance(g, Polygon) for g in sub_geoms):
                return MultiPolygon(sub_geoms)
            elif all(isinstance(g, LineString) for g in sub_geoms):
                return MultiLineString(sub_geoms)
            elif all(isinstance(g, Point) for g in sub_geoms):
                return MultiPoint(sub_geoms)
            else:
                return GeometryCollection(sub_geoms)

        return None

    @classmethod
    def _extract_placemark_properties(cls, placemark: Any) -> Dict[str, Any]:
        """Extracts metadata, description, and ExtendedData from a Placemark."""
        props: Dict[str, Any] = {}

        name_elem = placemark.find(".//{*}name")
        if name_elem is not None and name_elem.text:
            props["name"] = name_elem.text.strip()

        desc_elem = placemark.find(".//{*}description")
        if desc_elem is not None and desc_elem.text:
            props["description"] = desc_elem.text.strip()

        # Parse ExtendedData <Data name="xyz"><value>abc</value></Data>
        for data_elem in placemark.findall(".//{*}ExtendedData//{*}Data"):
            attr_name = data_elem.attrib.get("name")
            val_elem = data_elem.find(".//{*}value")
            if attr_name and val_elem is not None and val_elem.text:
                props[attr_name] = val_elem.text.strip()

        # Parse SchemaData <SimpleData name="xyz">abc</SimpleData>
        for sdata_elem in placemark.findall(".//{*}SchemaData//{*}SimpleData"):
            attr_name = sdata_elem.attrib.get("name")
            if attr_name and sdata_elem.text:
                props[attr_name] = sdata_elem.text.strip()

        return props

    @classmethod
    def parse_kml_bytes(
        cls, kml_content: bytes
    ) -> Tuple[List[Dict[str, Any]], pyproj.CRS]:
        """
        Parses raw KML bytes into extracted feature dictionaries and source CRS.

        Returns:
            Tuple of (features_list, pyproj.CRS)
        """
        import re
        # Pre-sanitize unescaped ampersands commonly found in user-generated KML files
        text = kml_content.decode("utf-8", errors="ignore")
        sanitized_text = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)", "&amp;", text)
        try:
            root = ET.fromstring(sanitized_text.encode("utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to parse XML content in KML file: {str(e)}")

        source_crs = pyproj.CRS.from_epsg(4326)
        features: List[Dict[str, Any]] = []

        # Find all Placemark elements anywhere in the document
        placemarks = root.findall(".//{http://www.opengis.net/kml/2.2}Placemark") or root.findall(".//{*}Placemark")

        feature_index = 0
        for pm in placemarks:
            props = cls._extract_placemark_properties(pm)

            # Search for direct or child geometry tags
            geometry_found: Optional[BaseGeometry] = None
            for child in pm:
                child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if child_tag in ("Polygon", "LineString", "Point", "MultiGeometry"):
                    geometry_found = cls._parse_geometry(child)
                    if geometry_found is not None:
                        break

            if geometry_found is not None:
                features.append({
                    "id": props.get("name") or f"feature_{feature_index}",
                    "geometry": geometry_found,
                    "properties": props,
                })
                feature_index += 1

        return features, source_crs
