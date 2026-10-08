"""API Route handlers for Geospatial File Measurement."""

from typing import List
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from app.config import settings
from app.models.schemas import (
    FileInfoResponse,
    FileListResponse,
    HealthResponse,
    MeasurementsResponse,
)
from app.services.file_processor import FileProcessor
from app.storage.file_store import file_store

router = APIRouter(prefix="/api", tags=["Geospatial Files"])


@router.post(
    "/files/",
    response_model=FileInfoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a geospatial file",
    description="Upload a .kml file or a .zip archive containing an ESRI Shapefile (.shp, .dbf, .prj).",
)
async def upload_file(file: UploadFile = File(...)):
    """Accepts a geospatial file (.zip Shapefile or .kml) and processes measurements."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing in upload request.",
        )

    filename_lower = file.filename.lower()
    if not (filename_lower.endswith(".kml") or filename_lower.endswith(".zip")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload either a .kml file or a .zip containing an ESRI Shapefile.",
        )

    # Read file content with size limit check
    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.max_upload_size_mb} MB.",
        )

    try:
        file_info, _ = FileProcessor.process_file_bytes(file.filename, content)
        return file_info
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing geospatial file: {str(e)}",
        )


@router.get(
    "/files/{file_id}/",
    response_model=FileInfoResponse,
    summary="Get file information",
    description="Returns metadata about an uploaded geospatial file including feature count, CRS, and status.",
)
async def get_file_info(file_id: str):
    """Retrieve file metadata adhering to assignment format."""
    file_info = file_store.get_file(file_id)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found.",
        )
    return file_info


@router.get(
    "/files/{file_id}/measurements/",
    response_model=MeasurementsResponse,
    summary="Get geometric measurements",
    description="Returns calculated measurements (area for Polygons, length for LineStrings) with projected CRS details.",
)
async def get_file_measurements(file_id: str):
    """Retrieve detailed feature measurements and summary statistics for a file."""
    file_info = file_store.get_file(file_id)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found.",
        )

    measurements = file_store.get_measurements(file_id)
    if not measurements:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Measurements for file ID '{file_id}' are unavailable or processing failed.",
        )
    return measurements


@router.get(
    "/files/",
    response_model=FileListResponse,
    summary="List all uploaded files",
    description="Returns a list of all tracked geospatial files and their processing status.",
)
async def list_files():
    """List all uploaded files."""
    files = file_store.list_files()
    return FileListResponse(total=len(files), files=files)


@router.delete(
    "/files/{file_id}/",
    status_code=status.HTTP_200_OK,
    summary="Delete a file",
    description="Deletes a file and its associated measurements from the registry.",
)
async def delete_file(file_id: str):
    """Delete a file by its ID."""
    deleted = file_store.delete_file(file_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found.",
        )
    return {"message": f"File '{file_id}' successfully deleted."}


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Service health check",
)
async def health_check():
    """Health check endpoint reporting API status and configuration."""
    return HealthResponse(
        status="HEALTHY",
        version=settings.app_version,
        supported_formats=[".kml", ".zip (Shapefile)"],
        default_crs=settings.default_source_crs,
    )
