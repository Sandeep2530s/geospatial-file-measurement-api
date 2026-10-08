"""Thread-safe storage registry for file records and measurements."""

import json
import sqlite3
import threading
from typing import Dict, List, Optional
from app.config import settings
from app.models.schemas import FileInfoResponse, FileStatus, MeasurementsResponse


class FileStore:
    """Thread-safe persistent store for geospatial files and computed measurements."""

    def __init__(self, db_path: Optional[str] = None):
        self._lock = threading.Lock()
        self.db_path = db_path or settings.sqlite_db_path
        self._memory_files: Dict[str, FileInfoResponse] = {}
        self._memory_measurements: Dict[str, MeasurementsResponse] = {}
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize SQLite tables for persistent storage across restarts."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS files (
                        id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        feature_count INTEGER NOT NULL,
                        crs TEXT NOT NULL,
                        status TEXT NOT NULL,
                        error_message TEXT
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS measurements (
                        file_id TEXT PRIMARY KEY,
                        data_json TEXT NOT NULL,
                        FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
                    );
                """)
                conn.commit()

            # Pre-load records into memory cache
            self._reload_cache()

    def _reload_cache(self) -> None:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM files").fetchall()
            for r in rows:
                self._memory_files[r["id"]] = FileInfoResponse(
                    id=r["id"],
                    filename=r["filename"],
                    feature_count=r["feature_count"],
                    crs=r["crs"],
                    status=FileStatus(r["status"]),
                    error_message=r["error_message"],
                )
            m_rows = conn.execute("SELECT file_id, data_json FROM measurements").fetchall()
            for mr in m_rows:
                try:
                    data = json.loads(mr["data_json"])
                    self._memory_measurements[mr["file_id"]] = MeasurementsResponse(**data)
                except Exception:
                    pass

    def save_file(
        self,
        file_info: FileInfoResponse,
        measurements: Optional[MeasurementsResponse] = None,
    ) -> None:
        """Save or update file metadata and its measurements."""
        with self._lock:
            self._memory_files[file_info.id] = file_info
            if measurements:
                self._memory_measurements[file_info.id] = measurements

            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO files (id, filename, feature_count, crs, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (
                    file_info.id,
                    file_info.filename,
                    file_info.feature_count,
                    file_info.crs,
                    file_info.status.value,
                    file_info.error_message,
                ))
                if measurements:
                    conn.execute("""
                        INSERT OR REPLACE INTO measurements (file_id, data_json)
                        VALUES (?, ?);
                    """, (
                        file_info.id,
                        measurements.model_dump_json(),
                    ))
                conn.commit()

    def get_file(self, file_id: str) -> Optional[FileInfoResponse]:
        """Retrieve file metadata by ID."""
        with self._lock:
            return self._memory_files.get(file_id)

    def get_measurements(self, file_id: str) -> Optional[MeasurementsResponse]:
        """Retrieve computed measurements for a file ID."""
        with self._lock:
            return self._memory_measurements.get(file_id)

    def list_files(self) -> List[FileInfoResponse]:
        """List all tracked files."""
        with self._lock:
            return list(self._memory_files.values())

    def delete_file(self, file_id: str) -> bool:
        """Delete file and its associated measurements."""
        with self._lock:
            existed = file_id in self._memory_files
            self._memory_files.pop(file_id, None)
            self._memory_measurements.pop(file_id, None)

            with self._get_connection() as conn:
                conn.execute("DELETE FROM measurements WHERE file_id = ?", (file_id,))
                conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
                conn.commit()

            return existed

    def clear(self) -> None:
        """Clear all stored data (primarily for test resets)."""
        with self._lock:
            self._memory_files.clear()
            self._memory_measurements.clear()
            with self._get_connection() as conn:
                conn.execute("DELETE FROM measurements")
                conn.execute("DELETE FROM files")
                conn.commit()


file_store = FileStore()
