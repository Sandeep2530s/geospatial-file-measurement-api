"""Unit tests for measurement calculation service."""

import pyproj
from shapely.geometry import Polygon, LineString, Point, GeometryCollection
from app.models.schemas import MeasurementType
from app.services.measurement_service import MeasurementService


def test_polygon_measurement():
    poly = Polygon([(77.5850, 12.9650), (77.5950, 12.9650), (77.5950, 12.9750), (77.5850, 12.9750), (77.5850, 12.9650)])
    src_crs = pyproj.CRS.from_epsg(4326)

    meas = MeasurementService.calculate_feature_measurement(
        feature_id="poly_1",
        geometry=poly,
        source_crs=src_crs,
        properties={"zone": "quarry"},
    )

    assert meas.feature_id == "poly_1"
    assert meas.geometry_type == "Polygon"
    assert meas.measurement.type == MeasurementType.AREA
    assert meas.measurement.area is not None
    assert meas.measurement.area.square_meters > 0
    assert meas.measurement.area.hectares > 0
    assert "m²" in meas.measurement.area.formatted
    assert meas.properties["zone"] == "quarry"


def test_linestring_measurement():
    line = LineString([(77.5850, 12.9650), (77.5900, 12.9670), (77.5950, 12.9700)])
    src_crs = pyproj.CRS.from_epsg(4326)

    meas = MeasurementService.calculate_feature_measurement(
        feature_id="line_1",
        geometry=line,
        source_crs=src_crs,
        properties={"road": "haul_route"},
    )

    assert meas.feature_id == "line_1"
    assert meas.geometry_type == "LineString"
    assert meas.measurement.type == MeasurementType.LENGTH
    assert meas.measurement.length is not None
    assert meas.measurement.length.meters > 0
    assert meas.measurement.length.kilometers > 0
    assert "m" in meas.measurement.length.formatted


def test_point_graceful_handling():
    point = Point(77.5900, 12.9700)
    src_crs = pyproj.CRS.from_epsg(4326)

    meas = MeasurementService.calculate_feature_measurement(
        feature_id="pt_1",
        geometry=point,
        source_crs=src_crs,
        properties={"label": "GCP"},
    )

    assert meas.feature_id == "pt_1"
    assert meas.geometry_type == "Point"
    assert meas.measurement.type == MeasurementType.NONE
    assert meas.measurement.area is None
    assert meas.measurement.length is None
    assert "not required" in meas.notes.lower()


def test_unsupported_geometry_graceful_handling():
    geom_coll = GeometryCollection([Point(0, 0), LineString([(0, 0), (1, 1)])])
    src_crs = pyproj.CRS.from_epsg(4326)

    meas = MeasurementService.calculate_feature_measurement(
        feature_id="unsupported_1",
        geometry=geom_coll,
        source_crs=src_crs,
    )

    assert meas.measurement.type == MeasurementType.NONE
    assert "not supported" in meas.measurement.remarks.lower()


def test_dataset_summary():
    poly = Polygon([(77.5850, 12.9650), (77.5950, 12.9650), (77.5950, 12.9750), (77.5850, 12.9750), (77.5850, 12.9650)])
    line = LineString([(77.5850, 12.9650), (77.5950, 12.9750)])
    point = Point(77.5900, 12.9700)
    src_crs = pyproj.CRS.from_epsg(4326)

    m1 = MeasurementService.calculate_feature_measurement("f1", poly, src_crs)
    m2 = MeasurementService.calculate_feature_measurement("f2", line, src_crs)
    m3 = MeasurementService.calculate_feature_measurement("f3", point, src_crs)

    summary = MeasurementService.calculate_dataset_summary([m1, m2, m3], primary_target_crs="EPSG:32643")

    assert summary.total_features == 3
    assert summary.polygon_count == 1
    assert summary.total_area_sq_meters > 0
    assert summary.linestring_count == 1
    assert summary.total_length_meters > 0
    assert summary.point_count == 1
    assert summary.target_projected_crs == "EPSG:32643"
