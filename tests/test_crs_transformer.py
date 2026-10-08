"""Unit tests for CRS Transformer and Projection Engine."""

import pytest
import pyproj
from shapely.geometry import Polygon, LineString, Point
from app.services.crs_transformer import CRSTransformer


def test_parse_crs():
    crs_4326 = CRSTransformer.parse_crs("EPSG:4326")
    assert crs_4326.to_epsg() == 4326

    crs_none = CRSTransformer.parse_crs(None)
    assert crs_none.to_epsg() == 4326

    crs_invalid = CRSTransformer.parse_crs("NOT_A_VALID_CRS")
    assert crs_invalid.to_epsg() == 4326


def test_optimal_projected_crs_selection_northern():
    # Bengaluru coordinates (77.5946 E, 12.9716 N) -> UTM Zone 43N (EPSG:32643)
    poly = Polygon([(77.58, 12.96), (77.60, 12.96), (77.60, 12.98), (77.58, 12.98), (77.58, 12.96)])
    src_crs = pyproj.CRS.from_epsg(4326)

    target_crs = CRSTransformer.get_optimal_projected_crs(poly, src_crs)
    assert target_crs.to_epsg() == 32643


def test_optimal_projected_crs_selection_southern():
    # Sydney, Australia coordinates (151.2 E, -33.8 S) -> UTM Zone 56S (EPSG:32756)
    poly = Polygon([(151.20, -33.86), (151.22, -33.86), (151.22, -33.84), (151.20, -33.84), (151.20, -33.86)])
    src_crs = pyproj.CRS.from_epsg(4326)

    target_crs = CRSTransformer.get_optimal_projected_crs(poly, src_crs)
    assert target_crs.to_epsg() == 32756


def test_already_projected_preservation():
    # If already in UTM 43N, preserve it
    poly = Polygon([(500000, 1400000), (501000, 1400000), (501000, 1401000), (500000, 1401000)])
    utm_crs = pyproj.CRS.from_epsg(32643)

    target_crs = CRSTransformer.get_optimal_projected_crs(poly, utm_crs)
    assert target_crs.to_epsg() == 32643


def test_reproject_geometry_polygon():
    # 0.01 degree square in Bengaluru is approx 1.1 km x 1.1 km = ~1.2 million m²
    poly = Polygon([(77.59, 12.97), (77.60, 12.97), (77.60, 12.98), (77.59, 12.98), (77.59, 12.97)])
    src_crs = pyproj.CRS.from_epsg(4326)

    projected, target_crs_str = CRSTransformer.reproject_geometry(poly, src_crs)

    assert "32643" in target_crs_str
    assert projected.is_valid
    # Area should be roughly ~1,200,000 m² (positive and realistic metric value)
    assert 1_100_000 < projected.area < 1_300_000


def test_reproject_geometry_linestring():
    line = LineString([(77.59, 12.97), (77.60, 12.98)])
    src_crs = pyproj.CRS.from_epsg(4326)

    projected, target_crs_str = CRSTransformer.reproject_geometry(line, src_crs)

    assert "32643" in target_crs_str
    assert projected.is_valid
    # Diagonal length across ~1.1 km x 1.1 km is approx 1.55 km (1550 meters)
    assert 1400 < projected.length < 1700
