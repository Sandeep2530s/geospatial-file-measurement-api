"""Configuration settings for the Geospatial File Measurement API."""

import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(env_prefix="GEO_", env_file=".env", extra="ignore")

    app_name: str = "Geospatial File Measurement API"
    app_version: str = "1.0.0"
    app_description: str = (
        "Enterprise-grade backend API for uploading, processing, and calculating "
        "measurements for geospatial files (ESRI Shapefiles and KML) with dynamic CRS reprojection."
    )
    debug: bool = False

    # Upload and file constraints
    max_upload_size_mb: int = 50
    allowed_extensions: list[str] = Field(default_factory=lambda: [".zip", ".kml"])
    temp_upload_dir: Path = Path(os.getenv("TEMP_UPLOAD_DIR", "temp_uploads"))

    # Default Geographic CRS when unprojected / not specified in .prj
    default_source_crs: str = "EPSG:4326"

    # Database
    sqlite_db_path: str = "geospatial_measurements.db"


settings = Settings()

# Ensure temp directory exists
settings.temp_upload_dir.mkdir(parents=True, exist_ok=True)
