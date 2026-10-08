"""Script to generate test ESRI Shapefiles (.zip) with WGS84 and projected UTM coordinates."""

import io
import os
import zipfile
from pathlib import Path
import pyproj
import shapefile


def create_wgs84_shapefile_zip(output_path: Path):
    """Creates a sample shapefile in geographic CRS (EPSG:4326)."""
    shp_buf = io.BytesIO()
    shx_buf = io.BytesIO()
    dbf_buf = io.BytesIO()

    # Writer for Polygons (exterior ring clockwise for shapefile)
    w = shapefile.Writer(shp=shp_buf, shx=shx_buf, dbf=dbf_buf, shapeType=shapefile.POLYGON)
    w.field("NAME", "C", size=50)
    w.field("ZONE_TYPE", "C", size=30)
    w.field("SURVEY_ID", "C", size=20)

    # Polygon 1: Bengaluru Mining Zone 1
    w.poly([[[77.5850, 12.9750], [77.5950, 12.9750], [77.5950, 12.9650], [77.5850, 12.9650], [77.5850, 12.9750]]])
    w.record("Pit Sector 1", "Active Mining", "SRV-001")

    # Polygon 2: Bengaluru Waste Dump Area
    w.poly([[[77.5960, 12.9730], [77.6030, 12.9730], [77.6030, 12.9670], [77.5960, 12.9670], [77.5960, 12.9730]]])
    w.record("Overburden Dump", "Waste Storage", "SRV-002")

    w.close()

    prj_wkt = pyproj.CRS.from_epsg(4326).to_wkt()

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mining_site_wgs84.shp", shp_buf.getvalue())
        zf.writestr("mining_site_wgs84.shx", shx_buf.getvalue())
        zf.writestr("mining_site_wgs84.dbf", dbf_buf.getvalue())
        zf.writestr("mining_site_wgs84.prj", prj_wkt)

    print(f"Created {output_path} ({os.path.getsize(output_path)} bytes)")


def create_utm_line_shapefile_zip(output_path: Path):
    """Creates a sample shapefile already projected in UTM 43N (EPSG:32643)."""
    shp_buf = io.BytesIO()
    shx_buf = io.BytesIO()
    dbf_buf = io.BytesIO()

    # Reproject Bengaluru coordinates to UTM 43N
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)

    w = shapefile.Writer(shp=shp_buf, shx=shx_buf, dbf=dbf_buf, shapeType=shapefile.POLYLINE)
    w.field("ROAD_NAME", "C", size=50)
    w.field("SURFACE", "C", size=30)

    # Line 1: Quarry access corridor
    lon_lats = [(77.5850, 12.9650), (77.5900, 12.9680), (77.5950, 12.9720), (77.6000, 12.9750)]
    utm_coords = [transformer.transform(lon, lat) for lon, lat in lon_lats]
    w.line([utm_coords])
    w.record("Access Road Alpha", "Paved Asphalt")

    # Line 2: Perimeter haul track
    lon_lats_2 = [(77.5800, 12.9600), (77.5820, 12.9630), (77.5850, 12.9650)]
    utm_coords_2 = [transformer.transform(lon, lat) for lon, lat in lon_lats_2]
    w.line([utm_coords_2])
    w.record("Perimeter Route Beta", "Unpaved Gravel")

    w.close()

    prj_wkt = pyproj.CRS.from_epsg(32643).to_wkt()

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("haul_roads_utm43n.shp", shp_buf.getvalue())
        zf.writestr("haul_roads_utm43n.shx", shx_buf.getvalue())
        zf.writestr("haul_roads_utm43n.dbf", dbf_buf.getvalue())
        zf.writestr("haul_roads_utm43n.prj", prj_wkt)

    print(f"Created {output_path} ({os.path.getsize(output_path)} bytes)")


def create_invalid_zip(output_path: Path):
    """Creates an invalid zip (missing .shp file) to test error handling."""
    with zipfile.ZipFile(output_path, "w") as zf:
        zf.writestr("readme.txt", "This is an empty archive without any shapefiles.")
    print(f"Created {output_path} ({os.path.getsize(output_path)} bytes)")


if __name__ == "__main__":
    out_dir = Path(__file__).parent
    create_wgs84_shapefile_zip(out_dir / "mining_site_wgs84.zip")
    create_utm_line_shapefile_zip(out_dir / "haul_roads_utm43n.zip")
    create_invalid_zip(out_dir / "invalid_archive.zip")
