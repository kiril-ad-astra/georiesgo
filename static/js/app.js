/* GeoRiesgo Caracas – app.js */

const NIVEL_ICONS  = { CRITICO:'🚨', ALTO:'⚠️', MODERADO:'🔶', BAJO:'✅' };
const NIVEL_COLORS = { CRITICO:'#FF4444', ALTO:'#FF8C00', MODERADO:'#FFD700', BAJO:'#4CAF50' };
const NIVEL_LABEL  = { CRITICO:'CRÍTICO', ALTO:'ALTO', MODERADO:'MODERADO', BAJO:'BAJO' };

// ── Map init ──────────────────────────────────────────────
const map = L.map('map', { center:[10.5000,-66.8800], zoom:12 });
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  attribution:'© OpenStreetMap © CARTO', maxZoom:19
}).addTo(map);

let currentPolygon=null, currentMarker=null;
const ZONE_COLORS = {
  valle_central:'#4CAF50', ladera_vulnerable:'#FFD700',
  cerro_pendiente:'#FF8C00', quebrada:'#FF4444', seguro:'#4CAF50'
};

// ── Load zones from API ───────────────────────────────────
fetch('/api/zones')
  .then(r=>{ if(!r.ok) throw new Error('HTTP '+r.status); return r.json(); })
  .then(zones=>{
    Object.entries(zones).forEach(([id,z])=>{
      const col = ZONE_COLORS[id]||'#888';
      L.polygon(z.polygon,{color:col,fillColor:col,fillOpacity:0.08,weight:1,dashArray:'4 4',opacity:0.5})
       .addTo(map)
       .on('click',()=>{ const r=document.querySelector(`input[name="zona"][value="${id}"]`); if(r)r.checked=true; });

      const icon = L.divIcon({
        className:'',
        html:`<div style="width:30px;height:30px;border-radius:50%;background:${col};border:2px solid rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#000;box-shadow:0 2px 8px rgba(0,0,0,.5)">${id.slice(0,2).toUpperCase()}</div>`,
        iconSize:[30,30],iconAnchor:[15,15]
      });
      L.marker(z.center,{icon}).addTo(map)
       .bindPopup(`<strong>${z.nombre}</strong><br><small style="color:#888">${z.descripcion}</small>`)
       .on('click',()=>{ const r=document.querySelector(`input[name="zona"][value="${id}"]`); if(r)r.checked=true; });
    });
  })
  .catch(e=>console.error('[ZONES]',e));

// ── Tabs ──────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn=>{
  btn.addEventListener('click',()=>{
    document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
    btn.classList.add('active');
    const p=document.getElementById('panel-'+btn.dataset.tab);
    if(p) p.classList.add('active');
  });
});

// ── Clima cards ───────────────────────────────────────────
function syncClima(){
  document.querySelectorAll('.clima-card').forEach(c=>{
    c.classList.toggle('active-clima', c.querySelector('input').checked);
  });
}
document.querySelectorAll('.clima-card').forEach(c=>{
  c.addEventListener('click',()=>{ c.querySelector('input').checked=true; syncClima(); });
});
syncClima();

// ── Analyze ────────────────────────────────────────────────
const btnAnalizar    = document.getElementById('btnAnalizar');
const loadingOverlay = document.getElementById('loadingOverlay');
const resultCard     = document.getElementById('resultCard');
const mapAlert       = document.getElementById('mapAlert');

btnAnalizar.addEventListener('click', async ()=>{
  const zona  = (document.querySelector('input[name="zona"]:checked')  ||{}).value||'valle_central';
  const clima = (document.querySelector('input[name="clima"]:checked') ||{}).value||'moderado';

  loadingOverlay.classList.remove('hidden');
  btnAnalizar.disabled=true;

  try {
    const res = await fetch('/api/analyze',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({zona,clima})
    });
    if(!res.ok){ const t=await res.text(); throw new Error('HTTP '+res.status+': '+t.slice(0,120)); }
    const data = await res.json();
    if(!data.ok) throw new Error(data.error||'Error del servidor');
    showResult(data);
    updateMap(data);
  } catch(err){
    console.error('[ANALYZE]',err);
    toast('❌','Error',err.message,8000);
  } finally {
    loadingOverlay.classList.add('hidden');
    btnAnalizar.disabled=false;
  }
});

// ── Show result ───────────────────────────────────────────
function showResult(d){
  const col   = NIVEL_COLORS[d.nivel]||'#888';
  const icon  = NIVEL_ICONS[d.nivel] ||'📊';
  const label = NIVEL_LABEL[d.nivel] ||d.nivel;
  const C=150.8;

  document.getElementById('resultBar').style.background=col;
  document.getElementById('resultIcon').textContent=icon;
  const nEl=document.getElementById('resultNivel');
  nEl.textContent='NIVEL '+label; nEl.style.color=col;
  document.getElementById('resultZonaNombre').textContent=d.zona_nombre;

  const arc=document.getElementById('probArc');
  arc.style.strokeDashoffset=C-(d.prob/100)*C;
  arc.style.stroke=col;
  document.getElementById('probNum').textContent=d.prob+'%';

  const fill=document.getElementById('progressFill');
  fill.style.width=d.prob+'%'; fill.style.background=col;

  document.getElementById('accionText').textContent=d.accion;
  const ab=document.getElementById('accionBox');
  ab.style.borderColor=col; ab.style.background=hexRgba(col,.08);

  document.getElementById('explicacionText').textContent=d.explicacion;
  document.getElementById('resultMetodo').textContent=d.metodo;
  document.getElementById('resultHora').textContent=d.hora;
  resultCard.classList.remove('hidden');
}

// ── Update map ────────────────────────────────────────────
function updateMap(d){
  if(currentPolygon){map.removeLayer(currentPolygon);currentPolygon=null;}
  if(currentMarker) {map.removeLayer(currentMarker); currentMarker=null;}

  const col=d.colors.fill;
  currentPolygon=L.polygon(d.zona_polygon,{color:d.colors.border,fillColor:col,fillOpacity:.45,weight:3}).addTo(map);
  pulsePolygon(currentPolygon);

  const label=NIVEL_LABEL[d.nivel]||d.nivel;
  const mIcon=L.divIcon({
    className:'',
    html:`<div style="width:44px;height:44px;border-radius:50%;background:${col};border:3px solid #fff;display:flex;align-items:center;justify-content:center;font-size:20px;box-shadow:0 0 0 4px ${hexRgba(col,.35)},0 4px 16px rgba(0,0,0,.5)">${NIVEL_ICONS[d.nivel]||'⚠️'}</div>`,
    iconSize:[44,44],iconAnchor:[22,22]
  });
  currentMarker=L.marker(d.zona_center,{icon:mIcon}).addTo(map)
    .bindPopup(`<div style="font-family:sans-serif;min-width:190px"><b style="font-size:15px">${NIVEL_ICONS[d.nivel]} ${label}</b><br><span style="color:#aaa">${d.zona_nombre}</span><br><span style="font-size:18px;font-weight:700;color:${col}">${d.prob}%</span><br><small style="color:#ccc">${d.accion}</small><hr style="border-color:#444;margin:6px 0"><small style="color:#888">${d.hora}</small></div>`,{maxWidth:250})
    .openPopup();

  map.flyTo(d.zona_center,13,{duration:1.2});
  toast(NIVEL_ICONS[d.nivel]||'⚠️', d.zona_nombre+' — Riesgo '+label+' ('+d.prob+'%)', d.accion, 6000);
}

// ── Pulse ─────────────────────────────────────────────────
function pulsePolygon(p){
  let n=0;
  const iv=setInterval(()=>{
    n++; p.setStyle({fillOpacity:n%2===0?.45:.15});
    if(n>=6){clearInterval(iv);p.setStyle({fillOpacity:.45});}
  },350);
}

// ── Toast ─────────────────────────────────────────────────
function toast(icon,title,sub,ms){
  document.getElementById('mapAlertIcon').textContent=icon;
  document.getElementById('mapAlertTitle').textContent=title;
  document.getElementById('mapAlertSub').textContent=sub;
  mapAlert.classList.remove('hidden');
  clearTimeout(window._t);
  window._t=setTimeout(()=>mapAlert.classList.add('hidden'),ms||5000);
}

// ── Clock ─────────────────────────────────────────────────
(function tick(){ const e=document.getElementById('headerClock'); if(e)e.textContent=new Date().toLocaleTimeString('es-VE',{hour12:false}); setTimeout(tick,1000); })();

// ── Util ──────────────────────────────────────────────────
function hexRgba(h,a){ const r=parseInt(h.slice(1,3),16),g=parseInt(h.slice(3,5),16),b=parseInt(h.slice(5,7),16); return `rgba(${r},${g},${b},${a})`; }
