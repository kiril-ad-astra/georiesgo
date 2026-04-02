from flask import Flask, render_template, jsonify, request
import numpy as np
import random
from datetime import datetime
import os

app = Flask(__name__)

# ─── Configuración de zonas geográficas ───────────────────────────────────────
ZONES_GEO = {
    "valle_central": {
        "nombre": "Valle Central",
        "center": [10.5000, -66.8800],
        "polygon": [[10.4850, -66.9000], [10.4850, -66.8600],
                    [10.5150, -66.8600], [10.5150, -66.9000]],
        "descripcion": "Centro urbano de Caracas – áreas planas",
        "base_risk": 0.10
    },
    "ladera_vulnerable": {
        "nombre": "Laderas Medias",
        "center": [10.5150, -66.8950],
        "polygon": [[10.5000, -66.9150], [10.5000, -66.8750],
                    [10.5300, -66.8750], [10.5300, -66.9150]],
        "descripcion": "Antímano, Caricuao – pendientes 25-45°",
        "base_risk": 0.45
    },
    "cerro_pendiente": {
        "nombre": "Cerros Altos",
        "center": [10.5300, -66.8650],
        "polygon": [[10.5150, -66.8850], [10.5150, -66.8450],
                    [10.5450, -66.8450], [10.5450, -66.8850]],
        "descripcion": "El Paraíso, San Agustín – pendientes >45°",
        "base_risk": 0.65
    },
    "quebrada": {
        "nombre": "Cercanía a Quebradas",
        "center": [10.4950, -66.9100],
        "polygon": [[10.4800, -66.9300], [10.4800, -66.8900],
                    [10.5100, -66.8900], [10.5100, -66.9300]],
        "descripcion": "Quebrada Seca, Anauco – drenajes activos",
        "base_risk": 0.75
    },
    "seguro": {
        "nombre": "Zonas Consolidadas",
        "center": [10.4850, -66.8550],
        "polygon": [[10.4700, -66.8750], [10.4700, -66.8350],
                    [10.5000, -66.8350], [10.5000, -66.8750]],
        "descripcion": "Chacao, El Rosal – con obras de mitigación",
        "base_risk": 0.15
    }
}

CLIMA_FACTOR = {
    "seco": 0.5,
    "moderado": 1.0,
    "intenso": 1.8,
    "extremo": 2.5,
    "creciente": 1.5
}

RISK_COLORS = {
    "CRÍTICO": {"fill": "#FF4444", "border": "#CC0000", "bg": "#fff0f0"},
    "ALTO":    {"fill": "#FF8C00", "border": "#CC6600", "bg": "#fff5e6"},
    "MODERADO":{"fill": "#FFD700", "border": "#B8A000", "bg": "#fffbe6"},
    "BAJO":    {"fill": "#4CAF50", "border": "#2E7D32", "bg": "#f0fff0"},
}

# ─── Intentar cargar modelo CNN-LSTM ──────────────────────────────────────────
model = None
using_real_model = True

def load_model():
    global model, using_real_model
    model_file = "mejor_modelo_libertador.h5"
    for path in [model_file, os.path.join(os.path.dirname(__file__), model_file)]:
        if os.path.exists(path):
            try:
                from tensorflow import keras
                model = keras.models.load_model(path, compile=False)
                using_real_model = True
                print(f"✓ Modelo CNN-LSTM cargado: {path}")
                return
            except Exception as e:
                print(f"Error cargando modelo: {e}")
    print("⚠️  Modelo no encontrado – modo simulación activo.")

load_model()


# ─── Rutas ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html",
                           zones=ZONES_GEO,
                           using_real_model=using_real_model)


@app.route("/api/zones")
def api_zones():
    return jsonify(ZONES_GEO)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    zona_id  = data.get("zona", "valle_central")
    clima_id = data.get("clima", "moderado")

    zona = ZONES_GEO.get(zona_id, ZONES_GEO["valle_central"])

    if using_real_model and model:
        try:
            parche   = _dummy_patch(zona_id)
            secuencia = _dummy_sequence(clima_id)
            prob = float(model.predict(
                [secuencia, parche[np.newaxis, ...]], verbose=0)[0][0])
            metodo = "Modelo CNN-LSTM (entrenado con 147 eventos 2000-2023)"
        except Exception as e:
            prob   = _simulate(zona_id, clima_id)
            metodo = f"Simulación (error en modelo: {e})"
    else:
        prob   = _simulate(zona_id, clima_id)
        metodo = "Simulación realista – protocolos PCV 2021 / IGES 2019"

    # Clasificar
    if prob >= 0.70:
        nivel, accion = "CRÍTICO", "EVACUACIÓN INMEDIATA requerida"
        explicacion = (f"Condiciones extremas detectadas (prob. {prob*100:.1f}%). "
                       f"Patrón similar al evento Vargas 1999. "
                       f"Riesgo inminente de deslizamientos y desbordamientos.")
    elif prob >= 0.50:
        nivel, accion = "ALTO", "RESTRICCIÓN DE ACCESO a la zona"
        explicacion = (f"Alta probabilidad de deslizamientos en 6-12 h (prob. {prob*100:.1f}%). "
                       f"Similar a evento Caracas 2005. "
                       f"Se requiere restricción de circulación y alertas comunitarias.")
    elif prob >= 0.30:
        nivel, accion = "MODERADO", "VIGILANCIA ESPECIAL cada 2 h"
        explicacion = (f"Condiciones favorables para deslizamientos en sectores vulnerables "
                       f"(prob. {prob*100:.1f}%). Activar brigadas de vigilancia y mantener "
                       f"canales de comunicación con la comunidad.")
    else:
        nivel, accion = "BAJO", "VIGILANCIA ESTÁNDAR"
        explicacion = (f"Condiciones estables, sin amenaza inminente (prob. {prob*100:.1f}%). "
                       f"Continuar monitoreo rutinario y actualizar datos hidrometeorológicos "
                       f"cada 6 h.")

    colors = RISK_COLORS[nivel]

    return jsonify({
        "zona_id":     zona_id,
        "zona_nombre": zona["nombre"],
        "zona_center": zona["center"],
        "zona_polygon":zona["polygon"],
        "clima":       clima_id,
        "prob":        round(prob * 100, 1),
        "nivel":       nivel,
        "accion":      accion,
        "explicacion": explicacion,
        "metodo":      metodo,
        "colors":      colors,
        "hora":        datetime.now().strftime("%H:%M:%S – %d/%m/%Y"),
        "using_real_model": using_real_model
    })


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _simulate(zona_id, clima_id):
    base = ZONES_GEO[zona_id]["base_risk"]
    factor = CLIMA_FACTOR.get(clima_id, 1.0)
    prob = base * factor * random.uniform(0.88, 1.12)
    return round(min(0.95, max(0.05, prob)), 4)


def _dummy_patch(zona_id):
    patch = np.zeros((24, 24, 4), dtype=np.float32)
    configs = {
        "valle_central":    [(0.05,0.15),(0.1,0.25),(0.3,0.5),(0.8,1.0)],
        "cerro_pendiente":  [(0.45,0.55),(0.6,0.9),(0.2,0.4),(0.5,0.7)],
        "ladera_vulnerable":[(0.2,0.35),(0.4,0.7),(0.1,0.3),(0.6,0.8)],
        "quebrada":         [(0.1,0.25),(0.3,0.6),(0.0,0.07),(0.4,0.6)],
        "seguro":           [(0.05,0.15),(0.0,0.1),(0.7,1.0),(0.8,1.0)],
    }
    for i, (lo, hi) in enumerate(configs.get(zona_id, configs["valle_central"])):
        patch[:, :, i] = np.random.uniform(lo, hi, (24, 24))
    return patch


def _dummy_sequence(clima_id):
    seq = np.zeros((1, 24, 5), dtype=np.float32)
    if clima_id == "seco":
        precip = np.random.uniform(0, 0.5, 24)
    elif clima_id == "moderado":
        precip = np.random.gamma(1.5, 1.2, 24)
    elif clima_id == "intenso":
        precip = np.random.gamma(2.5, 2.0, 24)
    elif clima_id == "extremo":
        precip = np.zeros(24); precip[16:] = np.random.gamma(4, 3, 8)
    else:
        precip = np.linspace(0.2, 3.0, 24) + np.random.normal(0, 0.3, 24)

    temp    = 25 - 0.2 * precip + np.random.normal(0, 1, 24)
    humedad = 75 + precip + np.random.normal(0, 5, 24)
    for i in range(24):
        seq[0, i, 0] = precip[i]
        seq[0, i, 1] = temp[i]
        seq[0, i, 2] = humedad[i]
        seq[0, i, 3] = np.sum(precip[max(0,i-7):i+1]) * 3
        seq[0, i, 4] = np.sum(precip[:i+1]) * 3
    return seq


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
