"""Pydantic schemas and data transfer models."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class FileStatus(str, Enum):
    """Lifecycle status of an uploaded geospatial file."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GeometryType(str, Enum):
    """Supported and recognized geometry types."""
    POLYGON = "Polygon"
    MULTIPOLYGON = "MultiPolygon"
    LINESTRING = "LineString"
    MULTILINESTRING = "MultiLineString"
    POINT = "Point"
    MULTIPOINT = "MultiPoint"
    GEOMETRYCOLLECTION = "GeometryCollection"
    UNSUPPORTED = "Unsupported"


class MeasurementType(str, Enum):
    """Type of geometric measurement performed."""
    AREA = "area"
    LENGTH = "length"
    NONE = "none"


class AreaMeasurement(BaseModel):
    """Area measurement details for Polygon / MultiPolygon."""
    square_meters: float = Field(..., description="Area in square meters (SI standard)")
    hectares: float = Field(..., description="Area in hectares (1 ha = 10,000 m²)")
    square_kilometers: float = Field(..., description="Area in square kilometers (1 km² = 1,000,000 m²)")
    formatted: str = Field(..., description="Human-readable formatted string")


class LengthMeasurement(BaseModel):
    """Length measurement details for LineString / MultiLineString."""
    meters: float = Field(..., description="Length in meters (SI standard)")
    kilometers: float = Field(..., description="Length in kilometers")
    formatted: str = Field(..., description="Human-readable formatted string")


class MeasurementDetail(BaseModel):
    """Unified container for measurement information."""
    type: MeasurementType
    area: Optional[AreaMeasurement] = None
    length: Optional[LengthMeasurement] = None
    remarks: Optional[str] = None


class FeatureMeasurement(BaseModel):
    """Measurement details for a single extracted geospatial feature."""
    feature_id: Union[int, str] = Field(..., description="Unique feature index or ID within the dataset")
    geometry_type: str = Field(..., description="Geometry type (Polygon, LineString, Point, etc.)")
    source_crs: str = Field(..., description="Source coordinate reference system of the feature")
    target_projected_crs: Optional[str] = Field(
        None, description="Projected CRS used to calculate distance/area (e.g., EPSG:32643 UTM Zone 43N)"
    )
    properties: Dict[str, Any] = Field(default_factory=dict, description="Feature attributes from DBF or KML ExtendedData")
    geometry: Optional[Dict[str, Any]] = Field(None, description="GeoJSON representation of the feature geometry")
    measurement: MeasurementDetail = Field(..., description="Calculated geometric measurements")
    notes: Optional[str] = Field(None, description="Special notes or graceful fallback description")


class MeasurementSummary(BaseModel):
    """Aggregated statistical summary of measurements across the dataset."""
    total_features: int = Field(0, description="Total number of features extracted")
    polygon_count: int = Field(0, description="Number of Polygon / MultiPolygon features")
    total_area_sq_meters: float = Field(0.0, description="Sum of all polygon areas in square meters")
    total_area_hectares: float = Field(0.0, description="Sum of all polygon areas in hectares")
    linestring_count: int = Field(0, description="Number of LineString / MultiLineString features")
    total_length_meters: float = Field(0.0, description="Sum of all linestring lengths in meters")
    total_length_km: float = Field(0.0, description="Sum of all linestring lengths in kilometers")
    point_count: int = Field(0, description="Number of Point / MultiPoint features")
    unsupported_count: int = Field(0, description="Features not eligible for measurement")
    target_projected_crs: Optional[str] = Field(None, description="Projected CRS used for dataset metrics")


class FileInfoResponse(BaseModel):
    """
    Standard response format strictly adhering to assignment specification:
    { "id": "abc123", "filename": "survey.kml", "feature_count": 120, "crs": "EPSG:4326", "status": "COMPLETED" }
    """
    id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original uploaded filename")
    feature_count: int = Field(..., description="Number of geospatial features extracted")
    crs: str = Field(..., description="Identified source Coordinate Reference System")
    status: FileStatus = Field(..., description="Processing status of the file")
    error_message: Optional[str] = Field(None, description="Error details if status is FAILED")


class MeasurementsResponse(BaseModel):
    """Detailed measurements response for a processed file."""
    file_id: str
    filename: str
    source_crs: str
    target_projected_crs: Optional[str]
    summary: MeasurementSummary
    features: List[FeatureMeasurement]


class FileListResponse(BaseModel):
    """Response containing a list of uploaded files."""
    total: int
    files: List[FileInfoResponse]


class HealthResponse(BaseModel):
    """Service health and diagnostic status."""
    status: str
    version: str
    supported_formats: List[str]
    default_crs: str
