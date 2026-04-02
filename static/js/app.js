/* ══════════════════════════════════════════════════════════
   GeoRiesgo Caracas – app.js
══════════════════════════════════════════════════════════ */

// ── Map init ──────────────────────────────────────────────
const map = L.map('map', {
  center: [10.5000, -66.8800],
  zoom: 12,
  zoomControl: true,
});

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  attribution: '© OpenStreetMap contributors © CARTO',
  maxZoom: 19,
}).addTo(map);

// ── State ─────────────────────────────────────────────────
let currentPolygon  = null;
let currentMarker   = null;
let allZoneMarkers  = {};
let contextPolygons = [];

// ── Zone colors (base) ───────────────────────────────────
const ZONE_BASE_COLORS = {
  valle_central:    '#4CAF50',
  ladera_vulnerable:'#FFD700',
  cerro_pendiente:  '#FF8C00',
  quebrada:         '#FF4444',
  seguro:           '#4CAF50',
};

// ── Draw context polygons (always visible) ────────────────
function drawContextPolygons(zones) {
  Object.entries(zones).forEach(([id, z]) => {
    const baseColor = ZONE_BASE_COLORS[id] || '#888';
    const poly = L.polygon(z.polygon, {
      color:       baseColor,
      fillColor:   baseColor,
      fillOpacity: 0.08,
      weight:      1,
      dashArray:   '4 4',
      opacity:     0.5,
    }).addTo(map);

    poly.on('click', () => {
      document.querySelector(`input[name="zona"][value="${id}"]`).checked = true;
      syncClimaCards();
    });

    contextPolygons.push(poly);
  });
}

// ── Zone markers ──────────────────────────────────────────
function addZoneMarkers(zones) {
  const icons = {
    valle_central:    { color: '#4CAF50', label: 'VC' },
    ladera_vulnerable:{ color: '#FFD700', label: 'LM' },
    cerro_pendiente:  { color: '#FF8C00', label: 'CA' },
    quebrada:         { color: '#FF4444', label: 'QA' },
    seguro:           { color: '#2196F3', label: 'ZC' },
  };

  Object.entries(zones).forEach(([id, z]) => {
    const cfg = icons[id] || { color: '#888', label: '?' };
    const icon = L.divIcon({
      className: '',
      html: `<div style="
        width:32px;height:32px;border-radius:50%;
        background:${cfg.color};border:2px solid rgba(0,0,0,0.5);
        display:flex;align-items:center;justify-content:center;
        font-family:'Rajdhani',sans-serif;font-size:11px;font-weight:700;
        color:#000;box-shadow:0 2px 8px rgba(0,0,0,0.5);
        cursor:pointer;
      ">${cfg.label}</div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });

    const marker = L.marker(z.center, { icon })
      .addTo(map)
      .bindPopup(`<strong>${z.nombre}</strong><br><span style="color:#8b949e;font-size:12px">${z.descripcion}</span>`);

    marker.on('click', () => {
      document.querySelector(`input[name="zona"][value="${id}"]`).checked = true;
    });

    allZoneMarkers[id] = marker;
  });
}

// ── Load zones from API ───────────────────────────────────
fetch('/api/zones')
  .then(r => r.json())
  .then(zones => {
    drawContextPolygons(zones);
    addZoneMarkers(zones);
  });

// ── Tab switching ─────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`panel-${btn.dataset.tab}`).classList.add('active');
  });
});

// ── Clima card sync ───────────────────────────────────────
function syncClimaCards() {
  document.querySelectorAll('.clima-card').forEach(card => {
    const inp = card.querySelector('input');
    card.classList.toggle('active-clima', inp.checked);
  });
}
document.querySelectorAll('.clima-card').forEach(card => {
  card.addEventListener('click', () => {
    card.querySelector('input').checked = true;
    syncClimaCards();
  });
});

// ── Analyze ────────────────────────────────────────────────
const btnAnalizar    = document.getElementById('btnAnalizar');
const loadingOverlay = document.getElementById('loadingOverlay');
const resultCard     = document.getElementById('resultCard');
const mapAlert       = document.getElementById('mapAlert');

btnAnalizar.addEventListener('click', async () => {
  const zona  = document.querySelector('input[name="zona"]:checked')?.value || 'valle_central';
  const clima = document.querySelector('input[name="clima"]:checked')?.value || 'moderado';

  // Show loading
  loadingOverlay.classList.remove('hidden');
  btnAnalizar.disabled = true;

  try {
    const res  = await fetch('/api/analyze', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ zona, clima }),
    });
    const data = await res.json();
    showResult(data);
    updateMap(data);
  } catch (err) {
    alert('Error al conectar con el servidor: ' + err.message);
  } finally {
    loadingOverlay.classList.add('hidden');
    btnAnalizar.disabled = false;
  }
});

// ── Display result ────────────────────────────────────────
const NIVEL_ICONS = { CRÍTICO: '🚨', ALTO: '⚠️', MODERADO: '🔶', BAJO: '✅' };
const NIVEL_COLORS = {
  CRÍTICO: '#FF4444',
  ALTO:    '#FF8C00',
  MODERADO:'#FFD700',
  BAJO:    '#4CAF50',
};

function showResult(data) {
  const color = NIVEL_COLORS[data.nivel] || '#888';
  const icon  = NIVEL_ICONS[data.nivel]  || '📊';
  const circum = 150.8; // 2πr, r=24

  // Bar color
  document.getElementById('resultBar').style.background = color;

  // Icon & level
  document.getElementById('resultIcon').textContent  = icon;
  document.getElementById('resultNivel').textContent = `NIVEL ${data.nivel}`;
  document.getElementById('resultNivel').style.color = color;
  document.getElementById('resultZonaNombre').textContent = data.zona_nombre;

  // Circle
  const offset = circum - (data.prob / 100) * circum;
  document.getElementById('probArc').style.strokeDashoffset = offset;
  document.getElementById('probArc').style.stroke = color;
  document.getElementById('probNum').textContent = data.prob + '%';

  // Progress bar
  const fill = document.getElementById('progressFill');
  fill.style.width      = data.prob + '%';
  fill.style.background = color;

  // Accion
  document.getElementById('accionText').textContent     = data.accion;
  document.getElementById('accionBox').style.borderColor = color;
  document.getElementById('accionBox').style.background  = hexToRgba(color, 0.08);

  // Explicacion
  document.getElementById('explicacionText').textContent = data.explicacion;

  // Meta
  document.getElementById('resultMetodo').textContent = data.metodo;
  document.getElementById('resultHora').textContent   = data.hora;

  // Show card
  resultCard.classList.remove('hidden');
}

// ── Update map ────────────────────────────────────────────
function updateMap(data) {
  // Remove previous risk polygon
  if (currentPolygon) { map.removeLayer(currentPolygon); currentPolygon = null; }
  if (currentMarker)  { map.removeLayer(currentMarker);  currentMarker  = null; }

  const color = data.colors.fill;

  // Draw risk polygon
  currentPolygon = L.polygon(data.zona_polygon, {
    color:       data.colors.border,
    fillColor:   color,
    fillOpacity: 0.45,
    weight:      3,
  }).addTo(map);

  // Pulse animation via repeated opacity change
  pulsePolygon(currentPolygon);

  // Marker
  const markerIcon = L.divIcon({
    className: '',
    html: `<div style="
      width:44px;height:44px;border-radius:50%;
      background:${color};border:3px solid white;
      display:flex;align-items:center;justify-content:center;
      font-size:20px;box-shadow:0 0 0 4px ${hexToRgba(color,0.35)},0 4px 16px rgba(0,0,0,0.5);
      animation:pulseMarker 1.5s ease-in-out 3;
    ">${NIVEL_ICONS[data.nivel] || '⚠️'}</div>`,
    iconSize:   [44, 44],
    iconAnchor: [22, 22],
  });

  currentMarker = L.marker(data.zona_center, { icon: markerIcon })
    .addTo(map)
    .bindPopup(`
      <div style="font-family:'Source Sans 3',sans-serif;min-width:200px">
        <div style="font-size:16px;font-weight:700;margin-bottom:4px">${NIVEL_ICONS[data.nivel]} Riesgo ${data.nivel}</div>
        <div style="font-size:14px;color:#aaa;margin-bottom:6px">${data.zona_nombre}</div>
        <div style="font-size:18px;font-weight:700;color:${color}">${data.prob}%</div>
        <div style="font-size:12px;color:#ccc;margin-top:6px">${data.accion}</div>
        <hr style="border-color:#333;margin:8px 0"/>
        <div style="font-size:11px;color:#888">${data.hora}</div>
      </div>
    `, { maxWidth: 260 })
    .openPopup();

  // Fly to zone
  map.flyTo(data.zona_center, 13, { duration: 1.2 });

  // Toast alert
  document.getElementById('mapAlertIcon').textContent  = NIVEL_ICONS[data.nivel] || '⚠️';
  document.getElementById('mapAlertTitle').textContent = `${data.zona_nombre} – Riesgo ${data.nivel} (${data.prob}%)`;
  document.getElementById('mapAlertSub').textContent   = data.accion;
  mapAlert.classList.remove('hidden');
  setTimeout(() => mapAlert.classList.add('hidden'), 6000);
}

// ── Pulse effect ──────────────────────────────────────────
function pulsePolygon(poly) {
  let count = 0;
  const origOpacity = 0.45;
  const interval = setInterval(() => {
    count++;
    const opacity = count % 2 === 0 ? origOpacity : 0.2;
    poly.setStyle({ fillOpacity: opacity });
    if (count >= 6) { clearInterval(interval); poly.setStyle({ fillOpacity: origOpacity }); }
  }, 400);
}

// ── Clock ─────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  document.getElementById('headerClock').textContent =
    now.toLocaleTimeString('es-VE', { hour12: false });
}
updateClock();
setInterval(updateClock, 1000);

// ── Helpers ───────────────────────────────────────────────
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// Inject pulse keyframe
const style = document.createElement('style');
style.textContent = `
  @keyframes pulseMarker {
    0%,100% { transform: scale(1); }
    50%      { transform: scale(1.25); }
  }
`;
document.head.appendChild(style);
