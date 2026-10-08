"""Main FastAPI application entrypoint with built-in interactive dashboard."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from app.api.routes import router
from app.config import settings
from app.ui import DASHBOARD_HTML

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core API routes
app.include_router(router)

SAMPLE_DIR = Path(__file__).parent.parent / "sample_data"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard():
    """Renders the self-contained interactive web dashboard (Zero external CDN dependencies)."""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/sample/kml", include_in_schema=False)
async def get_sample_kml():
    """Serves sample Bengaluru mining survey KML for 1-click testing."""
    kml_file = SAMPLE_DIR / "bangalore_mining_survey.kml"
    if kml_file.exists():
        return FileResponse(
            kml_file,
            media_type="application/vnd.google-earth.kml+xml",
            filename="bangalore_mining_survey.kml",
        )
    return Response(status_code=404)


@app.get("/sample/zip", include_in_schema=False)
async def get_sample_zip():
    """Serves sample WGS84 mining site Shapefile archive (.zip) for 1-click testing."""
    zip_file = SAMPLE_DIR / "mining_site_wgs84.zip"
    if zip_file.exists():
        return FileResponse(
            zip_file,
            media_type="application/zip",
            filename="mining_site_wgs84.zip",
        )
    return Response(status_code=404)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
