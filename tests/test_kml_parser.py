"""Unit tests for KML parser."""

from pathlib import Path
import pytest
from app.services.kml_parser import KMLParser

SAMPLE_KML_DIR = Path(__file__).parent.parent / "sample_data"


def test_parse_sample_kml_file():
    kml_file = SAMPLE_KML_DIR / "bangalore_mining_survey.kml"
    content = kml_file.read_bytes()

    features, src_crs = KMLParser.parse_kml_bytes(content)

    assert src_crs.to_epsg() == 4326
    assert len(features) == 4

    geom_types = [f["geometry"].geom_type for f in features]
    assert "Polygon" in geom_types
    assert "LineString" in geom_types
    assert "Point" in geom_types

    # Check properties extraction
    names = [f["properties"].get("name") for f in features]
    assert "Quarry Extraction Block A" in names
    assert "Primary Quarry Haul Road" in names
    assert "GCP Base Station Alpha" in names


def test_parse_invalid_xml_kml():
    invalid_content = b"<kml><broken_tag>unclosed</kml>"
    with pytest.raises(ValueError) as exc:
        KMLParser.parse_kml_bytes(invalid_content)
    assert "Failed to parse XML" in str(exc.value)
