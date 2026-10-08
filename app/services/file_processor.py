"""Unified processor for incoming geospatial files."""

import os
import uuid
from typing import Tuple
from app.models.schemas import (
    FileInfoResponse,
    FileStatus,
    MeasurementsResponse,
)
from app.services.crs_transformer import CRSTransformer
from app.services.kml_parser import KMLParser
from app.services.measurement_service import MeasurementService
from app.services.shapefile_parser import ShapefileParser
from app.storage.file_store import file_store


class FileProcessor:
    """Orchestrates validation, parsing, CRS reprojection, and measurement calculation."""

    @classmethod
    def process_file_bytes(
        cls,
        filename: str,
        content: bytes,
    ) -> Tuple[FileInfoResponse, MeasurementsResponse]:
        """
        Processes an uploaded geospatial file bytes (.kml or .zip shapefile).
        Stores metadata and computed measurements in the registry.
        """
        file_id = uuid.uuid4().hex[:8]  # Clean compact ID like "abc12345"
        ext = os.path.splitext(filename)[1].lower()

        # Step 1: Validate file extension
        if ext not in (".kml", ".zip"):
            file_info = FileInfoResponse(
                id=file_id,
                filename=filename,
                feature_count=0,
                crs="UNKNOWN",
                status=FileStatus.FAILED,
                error_message=f"Unsupported file format '{ext}'. Must be .kml or .zip containing Shapefile.",
            )
            file_store.save_file(file_info)
            raise ValueError(file_info.error_message)

        try:
            # Step 2: Parse features based on file type
            if ext == ".kml":
                raw_features, source_crs = KMLParser.parse_kml_bytes(content)
            else:  # .zip
                raw_features, source_crs = ShapefileParser.parse_zip_bytes(content)

            source_crs_str = f"EPSG:{source_crs.to_epsg()}" if source_crs.to_epsg() else source_crs.to_string()

            # Step 3: Compute measurements for every feature
            feature_measurements = []
            target_crs_used = None

            for feat in raw_features:
                f_id = feat["id"]
                geom = feat["geometry"]
                props = feat.get("properties", {})

                f_meas = MeasurementService.calculate_feature_measurement(
                    feature_id=f_id,
                    geometry=geom,
                    source_crs=source_crs,
                    properties=props,
                )
                if f_meas.target_projected_crs and not target_crs_used:
                    target_crs_used = f_meas.target_projected_crs

                feature_measurements.append(f_meas)

            # Step 4: Compute dataset-level summary
            summary = MeasurementService.calculate_dataset_summary(
                feature_measurements,
                primary_target_crs=target_crs_used or source_crs_str,
            )

            # Step 5: Construct response models
            file_info = FileInfoResponse(
                id=file_id,
                filename=filename,
                feature_count=len(feature_measurements),
                crs=source_crs_str,
                status=FileStatus.COMPLETED,
            )

            measurements_resp = MeasurementsResponse(
                file_id=file_id,
                filename=filename,
                source_crs=source_crs_str,
                target_projected_crs=target_crs_used,
                summary=summary,
                features=feature_measurements,
            )

            # Step 6: Persist in store
            file_store.save_file(file_info, measurements_resp)
            return file_info, measurements_resp

        except Exception as e:
            file_info = FileInfoResponse(
                id=file_id,
                filename=filename,
                feature_count=0,
                crs="UNKNOWN",
                status=FileStatus.FAILED,
                error_message=str(e),
            )
            file_store.save_file(file_info)
            raise
