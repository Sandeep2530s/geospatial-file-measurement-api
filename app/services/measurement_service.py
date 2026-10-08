"""Measurement calculation service for geospatial geometries."""

from typing import Any, Dict, List, Optional, Tuple, Union
import pyproj
from shapely.geometry.base import BaseGeometry
from shapely.geometry import (
    Polygon,
    MultiPolygon,
    LineString,
    MultiLineString,
    Point,
    MultiPoint,
    GeometryCollection,
)
from app.models.schemas import (
    AreaMeasurement,
    LengthMeasurement,
    MeasurementDetail,
    MeasurementType,
    FeatureMeasurement,
    MeasurementSummary,
)
from app.services.crs_transformer import CRSTransformer


class MeasurementService:
    """Calculates metric measurements for geometries after CRS reprojection."""

    @classmethod
    def calculate_feature_measurement(
        cls,
        feature_id: Union[int, str],
        geometry: BaseGeometry,
        source_crs: pyproj.CRS,
        properties: Optional[Dict[str, Any]] = None,
        target_projected_crs: Optional[pyproj.CRS] = None,
    ) -> FeatureMeasurement:
        """
        Calculates measurement for an individual feature.
        - Polygon / MultiPolygon: Reprojected Area (m², ha, km²)
        - LineString / MultiLineString: Reprojected Length (m, km)
        - Point / MultiPoint: Handled gracefully (no measurement)
        - Unsupported / Complex: Handled gracefully without crashing
        """
        geom_type = geometry.geom_type
        props = properties or {}
        source_crs_str = f"EPSG:{source_crs.to_epsg()}" if source_crs.to_epsg() else source_crs.to_string()

        # Handle empty geometries
        if geometry.is_empty:
            return FeatureMeasurement(
                feature_id=feature_id,
                geometry_type=geom_type,
                source_crs=source_crs_str,
                target_projected_crs=None,
                properties=props,
                geometry=None,
                measurement=MeasurementDetail(type=MeasurementType.NONE, remarks="Geometry is empty"),
                notes="Empty geometry encountered",
            )

        # 1. POLYGON / MULTIPOLYGON: Area calculation
        if isinstance(geometry, (Polygon, MultiPolygon)):
            projected_geom, target_crs_id = CRSTransformer.reproject_geometry(
                geometry, source_crs, target_projected_crs
            )
            area_sq_m = float(projected_geom.area)
            hectares = area_sq_m / 10000.0
            sq_km = area_sq_m / 1000000.0

            formatted_str = f"{area_sq_m:,.2f} m² ({hectares:,.4f} ha)"

            return FeatureMeasurement(
                feature_id=feature_id,
                geometry_type=geom_type,
                source_crs=source_crs_str,
                target_projected_crs=target_crs_id,
                properties=props,
                geometry=geometry.__geo_interface__,
                measurement=MeasurementDetail(
                    type=MeasurementType.AREA,
                    area=AreaMeasurement(
                        square_meters=round(area_sq_m, 3),
                        hectares=round(hectares, 5),
                        square_kilometers=round(sq_km, 6),
                        formatted=formatted_str,
                    ),
                ),
            )

        # 2. LINESTRING / MULTILINESTRING: Length calculation
        elif isinstance(geometry, (LineString, MultiLineString)):
            projected_geom, target_crs_id = CRSTransformer.reproject_geometry(
                geometry, source_crs, target_projected_crs
            )
            length_m = float(projected_geom.length)
            length_km = length_m / 1000.0

            formatted_str = f"{length_m:,.2f} m ({length_km:,.4f} km)"

            return FeatureMeasurement(
                feature_id=feature_id,
                geometry_type=geom_type,
                source_crs=source_crs_str,
                target_projected_crs=target_crs_id,
                properties=props,
                geometry=geometry.__geo_interface__,
                measurement=MeasurementDetail(
                    type=MeasurementType.LENGTH,
                    length=LengthMeasurement(
                        meters=round(length_m, 3),
                        kilometers=round(length_km, 5),
                        formatted=formatted_str,
                    ),
                ),
            )

        # 3. POINT / MULTIPOINT: Graceful handling (no measurement required per Requirement 4)
        elif isinstance(geometry, (Point, MultiPoint)):
            return FeatureMeasurement(
                feature_id=feature_id,
                geometry_type=geom_type,
                source_crs=source_crs_str,
                target_projected_crs=None,
                properties=props,
                geometry=geometry.__geo_interface__,
                measurement=MeasurementDetail(
                    type=MeasurementType.NONE,
                    remarks="Point features have zero dimensional length and area.",
                ),
                notes="Point feature - measurement not required per specification.",
            )

        # 4. UNSUPPORTED / GEOMETRYCOLLECTION: Graceful handling without crashing
        else:
            return FeatureMeasurement(
                feature_id=feature_id,
                geometry_type=geom_type,
                source_crs=source_crs_str,
                target_projected_crs=None,
                properties=props,
                geometry=geometry.__geo_interface__,
                measurement=MeasurementDetail(
                    type=MeasurementType.NONE,
                    remarks=f"Geometry type '{geom_type}' is not supported for measurement calculation.",
                ),
                notes="Unsupported geometry type handled gracefully.",
            )

    @classmethod
    def calculate_dataset_summary(
        cls,
        features: List[FeatureMeasurement],
        primary_target_crs: Optional[str] = None,
    ) -> MeasurementSummary:
        """Computes aggregated measurement metrics across the entire dataset."""
        poly_count = 0
        total_area = 0.0
        line_count = 0
        total_length = 0.0
        point_count = 0
        unsupported_count = 0

        for f in features:
            if f.measurement.type == MeasurementType.AREA and f.measurement.area:
                poly_count += 1
                total_area += f.measurement.area.square_meters
            elif f.measurement.type == MeasurementType.LENGTH and f.measurement.length:
                line_count += 1
                total_length += f.measurement.length.meters
            elif f.geometry_type in ("Point", "MultiPoint"):
                point_count += 1
            else:
                unsupported_count += 1

        total_area_ha = total_area / 10000.0
        total_len_km = total_length / 1000.0

        return MeasurementSummary(
            total_features=len(features),
            polygon_count=poly_count,
            total_area_sq_meters=round(total_area, 3),
            total_area_hectares=round(total_area_ha, 5),
            linestring_count=line_count,
            total_length_meters=round(total_length, 3),
            total_length_km=round(total_len_km, 5),
            point_count=point_count,
            unsupported_count=unsupported_count,
            target_projected_crs=primary_target_crs,
        )
