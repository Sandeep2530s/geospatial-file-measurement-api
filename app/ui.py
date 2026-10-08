"""Built-in standalone Web Dashboard with zero external CDN dependencies."""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AEREO - Geospatial File Measurement Platform</title>
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #151d30;
      --card-border: #1e293b;
      --primary: #0284c7;
      --primary-hover: #0369a1;
      --accent: #00f2fe;
      --teal: #059669;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --badge-poly: #0284c7;
      --badge-line: #8b5cf6;
      --badge-point: #f59e0b;
      --code-bg: #0f172a;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    body { background-color: var(--bg); color: var(--text); padding: 24px 16px; min-height: 100vh; }
    .container { max-width: 1100px; margin: 0 auto; }

    /* Header */
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--card-border); }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand-icon { width: 40px; height: 40px; background: linear-gradient(135deg, #0284c7, #00f2fe); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: bold; }
    .brand-title h1 { font-size: 20px; font-weight: 700; color: #fff; }
    .brand-title p { font-size: 13px; color: var(--text-muted); }
    .nav-links a { color: var(--text-muted); text-decoration: none; font-size: 13px; margin-left: 16px; transition: color 0.2s; padding: 6px 12px; border-radius: 6px; background: #1e293b; }
    .nav-links a:hover { color: #fff; background: #334155; }

    /* Layout */
    .grid { display: grid; grid-template-columns: 1fr; gap: 20px; }
    .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 24px; }
    .card-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }

    /* Upload Form */
    .drop-zone { border: 2px dashed #334155; border-radius: 10px; padding: 32px 20px; text-align: center; cursor: pointer; transition: all 0.2s; background: rgba(30, 41, 59, 0.4); margin-bottom: 16px; }
    .drop-zone:hover, .drop-zone.dragover { border-color: var(--accent); background: rgba(2, 132, 199, 0.1); }
    .drop-icon { font-size: 36px; margin-bottom: 8px; }
    .drop-text { font-size: 14px; color: var(--text-muted); }
    .drop-text strong { color: var(--accent); }
    .file-input { display: none; }
    .file-selected-name { font-size: 13px; color: #38bdf8; margin-top: 8px; font-weight: 500; }

    .btn-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    .btn { background: var(--primary); color: #fff; border: none; padding: 10px 20px; font-size: 14px; font-weight: 600; border-radius: 8px; cursor: pointer; transition: background 0.2s; }
    .btn:hover { background: var(--primary-hover); }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-secondary { background: #334155; }
    .btn-secondary:hover { background: #475569; }

    /* Stats Grid */
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }
    .stat-card { background: #1a233a; border: 1px solid var(--card-border); border-radius: 10px; padding: 16px; }
    .stat-label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 6px; }
    .stat-value { font-size: 22px; font-weight: 700; color: #fff; }
    .stat-sub { font-size: 12px; color: #38bdf8; margin-top: 4px; }

    /* Results Table */
    .table-container { overflow-x: auto; margin-top: 16px; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
    th { padding: 12px 14px; background: #1e293b; color: var(--text-muted); font-weight: 600; border-bottom: 1px solid var(--card-border); }
    td { padding: 12px 14px; border-bottom: 1px solid rgba(51, 65, 85, 0.4); vertical-align: middle; }
    tr:hover { background: rgba(30, 41, 59, 0.5); }

    /* Badges */
    .badge { display: inline-block; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
    .badge-polygon { background: rgba(2, 132, 199, 0.2); color: #38bdf8; border: 1px solid rgba(2, 132, 199, 0.4); }
    .badge-linestring { background: rgba(139, 92, 246, 0.2); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.4); }
    .badge-point { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
    .badge-status { background: rgba(5, 150, 105, 0.2); color: #34d399; border: 1px solid rgba(5, 150, 105, 0.4); }

    /* Alert / Messages */
    .alert { padding: 12px 16px; border-radius: 8px; font-size: 13px; margin-bottom: 16px; display: none; }
    .alert-error { background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; color: #fca5a5; }
    .alert-success { background: rgba(5, 150, 105, 0.15); border: 1px solid #10b981; color: #6ee7b7; }

    /* JSON Box */
    .json-box { background: var(--code-bg); border: 1px solid var(--card-border); border-radius: 8px; padding: 16px; max-height: 350px; overflow-y: auto; font-family: monospace; font-size: 12px; color: #e2e8f0; white-space: pre-wrap; word-break: break-all; margin-top: 16px; }

    .spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-radius: 50%; border-top-color: #fff; animation: spin 1s ease-in-out infinite; vertical-align: middle; margin-right: 6px; }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <div class="brand-icon">🛰️</div>
        <div class="brand-title">
          <h1>AEREO Geospatial Measurement Engine</h1>
          <p>Automated CRS Projection & Spatial Measurement API</p>
        </div>
      </div>
      <div class="nav-links">
        <a href="/api/health" target="_blank">Health Check</a>
        <a href="/openapi.json" target="_blank">OpenAPI JSON</a>
        <a href="/api/files/" target="_blank">List Files (API)</a>
      </div>
    </header>

    <div class="grid">
      <!-- Upload Card -->
      <div class="card">
        <div class="card-title">📁 Upload Geospatial File (.KML or .ZIP Shapefile)</div>
        
        <div id="alertBox" class="alert"></div>

        <div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
          <div class="drop-icon">📤</div>
          <div class="drop-text"><strong>Click to select</strong> or drag and drop your geospatial file here</div>
          <div class="drop-text" style="font-size: 12px; margin-top: 4px;">Supports ESRI Shapefile (.zip) or Keyhole Markup Language (.kml)</div>
          <div class="file-selected-name" id="fileNameDisplay"></div>
        </div>
        <input type="file" id="fileInput" class="file-input" accept=".kml,.zip">

        <div class="btn-row">
          <button class="btn" id="uploadBtn" onclick="uploadFile()">Process & Calculate Measurements</button>
          <span style="color: var(--text-muted); font-size: 13px;">or load test datasets:</span>
          <button class="btn btn-secondary" onclick="loadSampleKML()">Load Bengaluru KML</button>
          <button class="btn btn-secondary" onclick="loadSampleZip()">Load Mining Shapefile (.zip)</button>
        </div>
      </div>

      <!-- Results Card (Hidden initially) -->
      <div class="card" id="resultsCard" style="display: none;">
        <div class="card-title">
          <span>📊 Processing & Measurement Results</span>
          <span class="badge badge-status" id="fileStatusBadge">COMPLETED</span>
        </div>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">Total Features</div>
            <div class="stat-value" id="statFeatures">0</div>
            <div class="stat-sub" id="statSourceCrs">Source: EPSG:4326</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Total Polygon Area</div>
            <div class="stat-value" id="statArea">0 ha</div>
            <div class="stat-sub" id="statAreaM2">0 m²</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Total Haul Length</div>
            <div class="stat-value" id="statLength">0 km</div>
            <div class="stat-sub" id="statLengthM">0 m</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Target Projected CRS</div>
            <div class="stat-value" id="statTargetCrs" style="font-size: 18px; color: #38bdf8;">EPSG:32643</div>
            <div class="stat-sub">Auto UTM Zone Projection</div>
          </div>
        </div>

        <h3 style="font-size: 14px; margin-top: 16px; color: var(--text-muted);">EXTRACTED FEATURES & MEASUREMENTS</h3>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Feature ID / Name</th>
                <th>Geometry Type</th>
                <th>Calculated Measurement</th>
                <th>Projected CRS</th>
                <th>Attributes</th>
              </tr>
            </thead>
            <tbody id="featuresTableBody"></tbody>
          </table>
        </div>

        <div style="margin-top: 24px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4 style="font-size: 13px; color: var(--text-muted);">RAW API JSON RESPONSE</h4>
            <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="copyJson()">Copy JSON</button>
          </div>
          <div class="json-box" id="jsonOutput"></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let selectedFile = null;
    let latestResponseData = null;

    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const alertBox = document.getElementById('alertBox');
    const uploadBtn = document.getElementById('uploadBtn');

    // Drag and drop handlers
    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => { e.preventDefault(); dropZone.classList.add('dragover'); }, false);
    });
    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); }, false);
    });
    dropZone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt.files.length) handleFile(dt.files[0]);
    });
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length) handleFile(e.target.files[0]);
    });

    function handleFile(file) {
      selectedFile = file;
      fileNameDisplay.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      hideAlert();
    }

    function showAlert(msg, isError = false) {
      alertBox.textContent = msg;
      alertBox.className = isError ? 'alert alert-error' : 'alert alert-success';
      alertBox.style.display = 'block';
    }

    function hideAlert() { alertBox.style.display = 'none'; }

    async function uploadFile() {
      if (!selectedFile) {
        showAlert('Please choose a .kml or .zip shapefile to upload.', true);
        return;
      }

      uploadBtn.disabled = true;
      uploadBtn.innerHTML = '<span class="spinner"></span>Processing Geospatial Data...';
      hideAlert();

      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        const uploadRes = await fetch('/api/files/', { method: 'POST', body: formData });
        const uploadData = await uploadRes.json();

        if (!uploadRes.ok) {
          throw new Error(uploadData.detail || 'Upload failed');
        }

        showAlert(`File "${uploadData.filename}" processed successfully! Fetching measurements...`, false);

        // Fetch detailed measurements
        const measRes = await fetch(`/api/files/${uploadData.id}/measurements/`);
        const measData = await measRes.json();
        latestResponseData = measData;

        renderResults(measData);
      } catch (err) {
        showAlert(err.message, true);
      } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Process & Calculate Measurements';
      }
    }

    function renderResults(data) {
      document.getElementById('resultsCard').style.display = 'block';
      const sum = data.summary;

      document.getElementById('statFeatures').textContent = sum.total_features;
      document.getElementById('statSourceCrs').textContent = `Source: ${data.source_crs}`;
      document.getElementById('statArea').textContent = `${sum.total_area_hectares.toFixed(2)} ha`;
      document.getElementById('statAreaM2').textContent = `${sum.total_area_sq_meters.toLocaleString()} m²`;
      document.getElementById('statLength').textContent = `${sum.total_length_km.toFixed(2)} km`;
      document.getElementById('statLengthM').textContent = `${sum.total_length_meters.toLocaleString()} m`;
      document.getElementById('statTargetCrs').textContent = data.target_projected_crs || data.source_crs;

      const tbody = document.getElementById('featuresTableBody');
      tbody.innerHTML = '';

      data.features.forEach(f => {
        const tr = document.createElement('tr');

        let badgeClass = 'badge-polygon';
        if (f.geometry_type.includes('Line')) badgeClass = 'badge-linestring';
        if (f.geometry_type.includes('Point')) badgeClass = 'badge-point';

        let measText = '—';
        if (f.measurement.type === 'area' && f.measurement.area) {
          measText = `<strong>${f.measurement.area.formatted}</strong>`;
        } else if (f.measurement.type === 'length' && f.measurement.length) {
          measText = `<strong>${f.measurement.length.formatted}</strong>`;
        } else if (f.measurement.remarks) {
          measText = `<span style="color: var(--text-muted); font-size: 11px;">${f.measurement.remarks}</span>`;
        }

        const propsStr = Object.entries(f.properties)
          .map(([k, v]) => `<span style="color:#94a3b8">${k}:</span> ${v}`)
          .join('<br>') || '<span style="color:#64748b">—</span>';

        tr.innerHTML = `
          <td><strong>${f.feature_id}</strong></td>
          <td><span class="badge ${badgeClass}">${f.geometry_type}</span></td>
          <td>${measText}</td>
          <td><code style="background:#0f172a; padding:2px 6px; border-radius:4px; font-size:11px;">${f.target_projected_crs || f.source_crs}</code></td>
          <td style="font-size: 11px;">${propsStr}</td>
        `;
        tbody.appendChild(tr);
      });

      document.getElementById('jsonOutput').textContent = JSON.stringify(data, null, 2);
      document.getElementById('resultsCard').scrollIntoView({ behavior: 'smooth' });
    }

    function copyJson() {
      if (latestResponseData) {
        navigator.clipboard.writeText(JSON.stringify(latestResponseData, null, 2));
        alert('JSON copied to clipboard!');
      }
    }

    // Quick samples
    async function loadSampleKML() {
      showAlert('Loading sample KML...', false);
      const res = await fetch('/sample/kml');
      const blob = await res.blob();
      selectedFile = new File([blob], 'bangalore_mining_survey.kml', { type: 'application/vnd.google-earth.kml+xml' });
      fileNameDisplay.textContent = 'Selected: bangalore_mining_survey.kml (Sample Dataset)';
      uploadFile();
    }

    async function loadSampleZip() {
      showAlert('Loading sample Shapefile .zip...', false);
      const res = await fetch('/sample/zip');
      const blob = await res.blob();
      selectedFile = new File([blob], 'mining_site_wgs84.zip', { type: 'application/zip' });
      fileNameDisplay.textContent = 'Selected: mining_site_wgs84.zip (Sample Dataset)';
      uploadFile();
    }
  </script>
</body>
</html>
"""
