// Configuración del Mapa
const map = L.map('map').setView([10.5000, -66.8800], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

let currentPolygon = null;

// Lógica de Tabs
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn, .tab-panel').forEach(el => el.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`panel-${btn.dataset.tab}`).classList.add('active');
    });
});

// Función Principal de Análisis
document.getElementById('btnAnalizar').addEventListener('click', async () => {
    const zona = document.querySelector('input[name="zona"]:checked').value;
    const clima = document.querySelector('input[name="clima"]:checked').value;
    
    document.getElementById('loadingOverlay').classList.remove('hidden');

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ zona, clima })
        });
        const data = await response.json();

        if (data.ok) {
            // Actualizar UI
            document.getElementById('resultCard').classList.remove('hidden');
            document.getElementById('resultNivel').innerText = data.nivel;
            document.getElementById('resultZonaNombre').innerText = data.zona_nombre;
            document.getElementById('probNum').innerText = data.prob + '%';
            document.getElementById('accionText').innerText = data.accion;
            document.getElementById('explicacionText').innerText = data.explicacion;
            
            // Actualizar Mapa
            if (currentPolygon) map.removeLayer(currentPolygon);
            currentPolygon = L.polygon(data.zona_polygon, {
                color: data.colors.border,
                fillColor: data.colors.fill,
                fillOpacity: 0.6
            }).addTo(map);
            map.panTo(data.zona_center);
        }
    } catch (e) {
        alert("Error en la conexión con el servidor");
    } finally {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }
});
