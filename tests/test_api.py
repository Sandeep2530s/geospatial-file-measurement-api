"""End-to-end integration tests for FastAPI endpoints."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage.file_store import file_store

client = TestClient(app)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "sample_data"


@pytest.fixture(autouse=True)
def clean_storage():
    """Ensure clean storage before each test."""
    file_store.clear()
    yield
    file_store.clear()


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert ".kml" in data["supported_formats"]


def test_upload_kml_and_get_measurements():
    kml_path = SAMPLE_DATA_DIR / "bangalore_mining_survey.kml"

    # 1. POST /api/files/
    with open(kml_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("bangalore_mining_survey.kml", f, "application/vnd.google-earth.kml+xml")},
        )

    assert response.status_code == 201
    file_info = response.json()
    assert "id" in file_info
    file_id = file_info["id"]
    assert file_info["filename"] == "bangalore_mining_survey.kml"
    assert file_info["feature_count"] == 4
    assert file_info["crs"] == "EPSG:4326"
    assert file_info["status"] == "COMPLETED"

    # 2. GET /api/files/{id}/
    info_resp = client.get(f"/api/files/{file_id}/")
    assert info_resp.status_code == 200
    assert info_resp.json()["id"] == file_id
    assert info_resp.json()["feature_count"] == 4

    # 3. GET /api/files/{id}/measurements/
    meas_resp = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_resp.status_code == 200
    meas_data = meas_resp.json()
    assert meas_data["file_id"] == file_id
    assert meas_data["source_crs"] == "EPSG:4326"
    assert "EPSG:32643" in meas_data["target_projected_crs"]

    summary = meas_data["summary"]
    assert summary["total_features"] == 4
    assert summary["polygon_count"] == 2
    assert summary["total_area_sq_meters"] > 0
    assert summary["linestring_count"] == 1
    assert summary["total_length_meters"] > 0
    assert summary["point_count"] == 1

    # Check individual features
    features = meas_data["features"]
    assert len(features) == 4

    # Polygon feature has area
    poly_feat = next(f for f in features if f["geometry_type"] == "Polygon")
    assert poly_feat["measurement"]["type"] == "area"
    assert poly_feat["measurement"]["area"]["square_meters"] > 0
    assert poly_feat["measurement"]["area"]["hectares"] > 0

    # LineString feature has length
    line_feat = next(f for f in features if f["geometry_type"] == "LineString")
    assert line_feat["measurement"]["type"] == "length"
    assert line_feat["measurement"]["length"]["meters"] > 0

    # Point feature handled gracefully (no measurement)
    point_feat = next(f for f in features if f["geometry_type"] == "Point")
    assert point_feat["measurement"]["type"] == "none"
    assert point_feat["measurement"]["area"] is None
    assert point_feat["measurement"]["length"] is None


def test_upload_shapefile_wgs84():
    shp_path = SAMPLE_DATA_DIR / "mining_site_wgs84.zip"

    with open(shp_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("mining_site_wgs84.zip", f, "application/zip")},
        )

    assert response.status_code == 201
    file_info = response.json()
    assert file_info["feature_count"] == 2
    assert file_info["crs"] == "EPSG:4326"
    assert file_info["status"] == "COMPLETED"

    # Verify measurements
    file_id = file_info["id"]
    meas_resp = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_resp.status_code == 200
    meas_data = meas_resp.json()
    assert meas_data["summary"]["polygon_count"] == 2
    assert meas_data["summary"]["total_area_sq_meters"] > 0


def test_upload_shapefile_projected_utm():
    shp_path = SAMPLE_DATA_DIR / "haul_roads_utm43n.zip"

    with open(shp_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("haul_roads_utm43n.zip", f, "application/zip")},
        )

    assert response.status_code == 201
    file_info = response.json()
    assert file_info["feature_count"] == 2
    assert "32643" in file_info["crs"]

    meas_resp = client.get(f"/api/files/{file_info['id']}/measurements/")
    assert meas_resp.status_code == 200
    meas_data = meas_resp.json()
    assert meas_data["summary"]["linestring_count"] == 2
    assert meas_data["summary"]["total_length_meters"] > 0


def test_list_and_delete_files():
    kml_path = SAMPLE_DATA_DIR / "bangalore_mining_survey.kml"
    with open(kml_path, "rb") as f:
        resp = client.post("/api/files/", files={"file": ("survey.kml", f, "text/xml")})
    file_id = resp.json()["id"]

    # List files
    list_resp = client.get("/api/files/")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    # Delete file
    del_resp = client.delete(f"/api/files/{file_id}/")
    assert del_resp.status_code == 200

    # Verify 404 after deletion
    get_resp = client.get(f"/api/files/{file_id}/")
    assert get_resp.status_code == 404


def test_upload_unsupported_extension():
    response = client.post(
        "/api/files/",
        files={"file": ("document.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_upload_invalid_zip():
    bad_zip = SAMPLE_DATA_DIR / "invalid_archive.zip"
    with open(bad_zip, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("invalid_archive.zip", f, "application/zip")},
        )
    assert response.status_code == 400
    assert "No .shp file found" in response.json()["detail"]
