// Frontend logic: populate dropdowns, fetch real orbital data from the
// FastAPI backend, draw the ground track on a Leaflet map, render the
// passes table, and run the (fake) live telemetry simulation.

const satelliteSelect = document.getElementById("satellite-select");
const stationSelect = document.getElementById("station-select");

let map, groundTrackLayer, satelliteMarker, stationMarker;

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
  return res.json();
}

function initMap() {
  map = L.map("map", { worldCopyJump: true }).setView([15, 78], 3);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 10,
  }).addTo(map);
  groundTrackLayer = L.layerGroup().addTo(map);
}

// Ground tracks cross the +180/-180 date line; drawing one straight
// polyline across that jump produces a line that wraps the whole globe.
// Split into separate segments whenever consecutive points jump a lot.
function splitAtDateLine(points) {
  const segments = [];
  let current = [];
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    if (current.length > 0) {
      const prev = current[current.length - 1];
      if (Math.abs(p.lon - prev.lon) > 180) {
        segments.push(current);
        current = [];
      }
    }
    current.push(p);
  }
  if (current.length) segments.push(current);
  return segments;
}

async function loadGroundTrack(satelliteId) {
  const data = await fetchJSON(`/api/ground-track?satellite=${satelliteId}`);
  groundTrackLayer.clearLayers();

  const segments = splitAtDateLine(data.points);
  for (const seg of segments) {
    L.polyline(
      seg.map((p) => [p.lat, p.lon]),
      { color: "#4da3ff", weight: 2, opacity: 0.8 }
    ).addTo(groundTrackLayer);
  }

  const current = await fetchJSON(`/api/current-position?satellite=${satelliteId}`);
  const icon = L.divIcon({
    html: "🛰️",
    className: "sat-icon",
    iconSize: [24, 24],
  });
  if (satelliteMarker) groundTrackLayer.removeLayer(satelliteMarker);
  satelliteMarker = L.marker([current.lat, current.lon], { icon }).bindPopup(
    `${current.satellite}<br>Altitude: ${current.altitude_km} km`
  );
  satelliteMarker.addTo(groundTrackLayer);
}

async function loadStationMarker(stationId, stations) {
  const station = stations.find((s) => s.id === stationId);
  if (stationMarker) map.removeLayer(stationMarker);
  stationMarker = L.marker([station.lat, station.lon], {
    icon: L.divIcon({ html: "📡", className: "station-icon", iconSize: [22, 22] }),
  })
    .addTo(map)
    .bindPopup(`Ground station: ${station.name}`);
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s`;
}

function formatLocal(isoString) {
  return new Date(isoString).toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

async function loadPasses(satelliteId, stationId) {
  const statusEl = document.getElementById("passes-status");
  const table = document.getElementById("passes-table");
  const tbody = document.getElementById("passes-body");

  statusEl.hidden = false;
  statusEl.textContent = "Calculating passes from real orbital data…";
  table.hidden = true;

  const data = await fetchJSON(`/api/passes?satellite=${satelliteId}&station=${stationId}&days=7`);

  tbody.innerHTML = "";
  if (data.passes.length === 0) {
    statusEl.textContent = "No passes above 10° elevation in the next 7 days for this pair.";
    return;
  }

  for (const p of data.passes) {
    const tr = document.createElement("tr");
    const elevClass = p.max_elevation_deg >= 40 ? "elevation-good" : "elevation-ok";
    tr.innerHTML = `
      <td>${formatLocal(p.rise_time)}</td>
      <td class="${elevClass}">${p.max_elevation_deg.toFixed(1)}&deg;</td>
      <td>${formatLocal(p.set_time)}</td>
      <td>${formatDuration(p.duration_seconds)}</td>
    `;
    tbody.appendChild(tr);
  }
  statusEl.hidden = true;
  table.hidden = false;
}

async function refreshAll(stations) {
  const satelliteId = satelliteSelect.value;
  const stationId = stationSelect.value;
  await Promise.all([
    loadGroundTrack(satelliteId),
    loadStationMarker(stationId, stations),
    loadPasses(satelliteId, stationId),
  ]);
}

// ---- Mock live telemetry (fake data, just for UI preview) ----

let telemetryInterval = null;
let telemetryState = { battery: 87, temp: 21, signal: -75 };

function randomWalk(value, delta, min, max) {
  const next = value + (Math.random() * 2 - 1) * delta;
  return Math.max(min, Math.min(max, next));
}

function tickTelemetry() {
  telemetryState.battery = randomWalk(telemetryState.battery, 0.6, 20, 100);
  telemetryState.temp = randomWalk(telemetryState.temp, 1.5, -10, 45);
  telemetryState.signal = randomWalk(telemetryState.signal, 2, -95, -55);

  document.getElementById("tm-battery").textContent = `${telemetryState.battery.toFixed(1)}%`;
  document.getElementById("tm-temp").textContent = `${telemetryState.temp.toFixed(1)} °C`;
  document.getElementById("tm-signal").textContent = `${telemetryState.signal.toFixed(0)} dBm`;
  document.getElementById("tm-link").textContent =
    telemetryState.signal > -85 ? "LOCKED" : "WEAK";
}

function toggleTelemetry() {
  const btn = document.getElementById("telemetry-toggle");
  if (telemetryInterval) {
    clearInterval(telemetryInterval);
    telemetryInterval = null;
    btn.textContent = "Start pass simulation";
    document.getElementById("tm-link").textContent = "IDLE";
    return;
  }
  btn.textContent = "Stop pass simulation";
  tickTelemetry();
  telemetryInterval = setInterval(tickTelemetry, 2000);
}

// ---- Boot ----

async function init() {
  initMap();

  const [satellites, stations] = await Promise.all([
    fetchJSON("/api/satellites"),
    fetchJSON("/api/ground-stations"),
  ]);

  satelliteSelect.innerHTML = satellites
    .map((s) => `<option value="${s.id}" title="${s.description}">${s.name}</option>`)
    .join("");
  stationSelect.innerHTML = stations
    .map((s) => `<option value="${s.id}">${s.name}</option>`)
    .join("");

  satelliteSelect.addEventListener("change", () => refreshAll(stations));
  stationSelect.addEventListener("change", () => refreshAll(stations));
  document.getElementById("telemetry-toggle").addEventListener("click", toggleTelemetry);

  await refreshAll(stations);
}

init().catch((err) => {
  console.error(err);
  document.getElementById("passes-status").textContent = `Error: ${err.message}`;
});
