import os
import urllib.request
from pathlib import Path

static_dir = Path("app/static")
static_dir.mkdir(parents=True, exist_ok=True)

files = {
    "swagger-ui.min.css": "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.17.14/swagger-ui.min.css",
    "swagger-ui-bundle.min.js": "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.17.14/swagger-ui-bundle.min.js",
}

for name, url in files.items():
    dest = static_dir / name
    print(f"Downloading {name}...")
    with urllib.request.urlopen(url) as resp:
        dest.write_bytes(resp.read())
    print(f"Saved {name} ({dest.stat().st_size} bytes)")
