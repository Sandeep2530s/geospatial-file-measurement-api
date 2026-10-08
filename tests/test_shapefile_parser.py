"""Unit tests for Shapefile ZIP parser."""

from pathlib import Path
import pytest
from app.services.shapefile_parser import ShapefileParser

SAMPLE_DATA_DIR = Path(__file__).parent.parent / "sample_data"


def test_parse_wgs84_shapefile():
    zip_path = SAMPLE_DATA_DIR / "mining_site_wgs84.zip"
    content = zip_path.read_bytes()

    features, src_crs = ShapefileParser.parse_zip_bytes(content)

    assert src_crs.to_epsg() == 4326
    assert len(features) == 2
    assert all(f["geometry"].geom_type == "Polygon" for f in features)
    assert features[0]["properties"]["NAME"] == "Pit Sector 1"
    assert features[1]["properties"]["NAME"] == "Overburden Dump"


def test_parse_utm_shapefile():
    zip_path = SAMPLE_DATA_DIR / "haul_roads_utm43n.zip"
    content = zip_path.read_bytes()

    features, src_crs = ShapefileParser.parse_zip_bytes(content)

    assert src_crs.to_epsg() == 32643
    assert len(features) == 2
    assert all(f["geometry"].geom_type in ("LineString", "MultiLineString") for f in features)
    assert features[0]["properties"]["ROAD_NAME"] == "Access Road Alpha"


def test_parse_invalid_zip_missing_shp():
    zip_path = SAMPLE_DATA_DIR / "invalid_archive.zip"
    content = zip_path.read_bytes()

    with pytest.raises(ValueError) as exc:
        ShapefileParser.parse_zip_bytes(content)
    assert "No .shp file found" in str(exc.value)


def test_parse_corrupt_zip():
    corrupt_content = b"PK\x03\x04corruptedbytes"
    with pytest.raises(ValueError) as exc:
        ShapefileParser.parse_zip_bytes(corrupt_content)
    assert "valid or readable ZIP archive" in str(exc.value)
