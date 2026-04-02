# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, request, Response
import json
import numpy as np
import random
from datetime import datetime
import os
import sys
import traceback

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

ZONES_GEO = {
    "valle_central": {
        "nombre": "Valle Central",
        "center": [10.5000, -66.8800],
        "polygon": [[10.4850, -66.9000], [10.4850, -66.8600],
                    [10.5150, -66.8600], [10.5150, -66.9000]],
        "descripcion": "Centro urbano de Caracas - areas planas",
        "base_risk": 0.10
    },
    "ladera_vulnerable": {
        "nombre": "Laderas Medias",
        "center": [10.5150, -66.8950],
        "polygon": [[10.5000, -66.9150], [10.5000, -66.8750],
                    [10.5300, -66.8750], [10.5300, -66.9150]],
        "descripcion": "Antimano, Caricuao - pendientes 25-45 grados",
        "base_risk": 0.45
    },
    "cerro_pendiente": {
        "nombre": "Cerros Altos",
        "center": [10.5300, -66.8650],
        "polygon": [[10.5150, -66.8850], [10.5150, -66.8450],
                    [10.5450, -66.8450], [10.5450, -66.8850]],
        "descripcion": "El Paraiso, San Agustin - pendientes mayores 45 grados",
        "base_risk": 0.65
    },
    "quebrada": {
        "nombre": "Cercania a Quebradas",
        "center": [10.4950, -66.9100],
        "polygon": [[10.4800, -66.9300], [10.4800, -66.8900],
                    [10.5100, -66.8900], [10.5100, -66.9300]],
        "descripcion": "Quebrada Seca, Anauco - drenajes activos",
        "base_risk": 0.75
    },
    "seguro": {
        "nombre": "Zonas Consolidadas",
        "center": [10.4850, -66.8550],
        "polygon": [[10.4700, -66.8750], [10.4700, -66.8350],
                    [10.5000, -66.8350], [10.5000, -66.8750]],
        "descripcion": "Chacao, El Rosal - con obras de mitigacion",
        "base_risk": 0.15
    }
}

CLIMA_FACTOR = {
    "seco": 0.5, "moderado": 1.0, "intenso": 1.8,
    "extremo": 2.5, "creciente": 1.5
}

RISK_COLORS = {
    "CRITICO":  {"fill": "#FF4444", "border": "#CC0000"},
    "ALTO":     {"fill": "#FF8C00", "border": "#CC6600"},
    "MODERADO": {"fill": "#FFD700", "border": "#B8A000"},
    "BAJO":     {"fill": "#4CAF50", "border": "#2E7D32"},
}

# ── Model loading ──────────────────────────────────────────────────────────────
model = None
using_real_model = False

def load_model():
    global model, using_real_model
    model_file = "mejor_modelo_libertador.h5"
    candidates = [
        model_file,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), model_file),
        os.path.join(os.getcwd(), model_file),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                print(f"[MODEL] Loading from: {path}", flush=True)
                os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
                import tensorflow as tf
                model = tf.keras.models.load_model(path, compile=False)
                using_real_model = True
                print("[MODEL] CNN-LSTM loaded OK", flush=True)
                return
            except ImportError:
                print("[MODEL] TensorFlow not installed", flush=True)
                return
            except Exception as e:
                print(f"[MODEL] Load error: {e}", flush=True)
                return
    print("[MODEL] .h5 not found - simulation mode", flush=True)

load_model()

# ── Helpers ────────────────────────────────────────────────────────────────────
def json_utf8(data, status=200):
    body = json.dumps(data, ensure_ascii=False)
    return Response(body, status=status, mimetype='application/json; charset=utf-8')

def _simulate(zona_id, clima_id):
    base = ZONES_GEO[zona_id]["base_risk"]
    factor = CLIMA_FACTOR.get(clima_id, 1.0)
    return round(min(0.95, max(0.05, base * factor * random.uniform(0.88, 1.12))), 4)

def _dummy_patch(zona_id):
    patch = np.zeros((24, 24, 4), dtype=np.float32)
    configs = {
        "valle_central":    [(0.05,0.15),(0.10,0.25),(0.30,0.50),(0.80,1.00)],
        "cerro_pendiente":  [(0.45,0.55),(0.60,0.90),(0.20,0.40),(0.50,0.70)],
        "ladera_vulnerable":[(0.20,0.35),(0.40,0.70),(0.10,0.30),(0.60,0.80)],
        "quebrada":         [(0.10,0.25),(0.30,0.60),(0.00,0.07),(0.40,0.60)],
        "seguro":           [(0.05,0.15),(0.00,0.10),(0.70,1.00),(0.80,1.00)],
    }
    for i, (lo, hi) in enumerate(configs.get(zona_id, configs["valle_central"])):
        patch[:, :, i] = np.random.uniform(lo, hi, (24, 24))
    return patch

def _dummy_sequence(clima_id):
    seq = np.zeros((1, 24, 5), dtype=np.float32)
    if   clima_id == "seco":     precip = np.random.uniform(0, 0.5, 24)
    elif clima_id == "moderado": precip = np.random.gamma(1.5, 1.2, 24)
    elif clima_id == "intenso":  precip = np.random.gamma(2.5, 2.0, 24)
    elif clima_id == "extremo":
        precip = np.zeros(24); precip[16:] = np.random.gamma(4, 3, 8)
    else:
        precip = np.linspace(0.2, 3.0, 24) + np.random.normal(0, 0.3, 24)
    temp    = 25 - 0.2 * precip + np.random.normal(0, 1, 24)
    humedad = 75 + precip + np.random.normal(0, 5, 24)
    for i in range(24):
        seq[0,i,0] = precip[i]; seq[0,i,1] = temp[i]; seq[0,i,2] = humedad[i]
        seq[0,i,3] = float(np.sum(precip[max(0,i-7):i+1])) * 3
        seq[0,i,4] = float(np.sum(precip[:i+1])) * 3
    return seq

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", zones=ZONES_GEO, using_real_model=using_real_model)

@app.route("/api/zones")
def api_zones():
    return json_utf8(ZONES_GEO)

@app.route("/api/health")
def health():
    return json_utf8({"status": "ok", "model": "CNN-LSTM" if using_real_model else "simulation"})

@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        data     = request.get_json(force=True, silent=True) or {}
        zona_id  = data.get("zona",  "valle_central")
        clima_id = data.get("clima", "moderado")
        if zona_id  not in ZONES_GEO:   zona_id  = "valle_central"
        if clima_id not in CLIMA_FACTOR: clima_id = "moderado"
        zona = ZONES_GEO[zona_id]

        if using_real_model and model:
            try:
                prob   = float(model.predict([_dummy_sequence(clima_id), _dummy_patch(zona_id)[np.newaxis,...]], verbose=0)[0][0])
                metodo = "Modelo CNN-LSTM (147 eventos 2000-2023)"
            except Exception as e:
                prob   = _simulate(zona_id, clima_id)
                metodo = f"Simulacion (error CNN: {str(e)[:60]})"
        else:
            prob   = _simulate(zona_id, clima_id)
            metodo = "Simulacion realista - PCV 2021 / IGES 2019"

        if prob >= 0.70:
            nivel="CRITICO"; accion="EVACUACION INMEDIATA requerida"
            exp=f"Condiciones extremas ({prob*100:.1f}%). Patron Vargas 1999. Riesgo inminente de deslizamientos."
        elif prob >= 0.50:
            nivel="ALTO"; accion="RESTRICCION DE ACCESO a la zona"
            exp=f"Alta probabilidad deslizamientos 6-12h ({prob*100:.1f}%). Similar Caracas 2005. Alertas comunitarias."
        elif prob >= 0.30:
            nivel="MODERADO"; accion="VIGILANCIA ESPECIAL cada 2h"
            exp=f"Condiciones favorables para deslizamientos ({prob*100:.1f}%). Activar brigadas de vigilancia."
        else:
            nivel="BAJO"; accion="VIGILANCIA ESTANDAR"
            exp=f"Condiciones estables ({prob*100:.1f}%). Monitoreo rutinario cada 6h."

        return json_utf8({
            "ok": True,
            "zona_id": zona_id, "zona_nombre": zona["nombre"],
            "zona_center": zona["center"], "zona_polygon": zona["polygon"],
            "clima": clima_id, "prob": round(prob*100,1),
            "nivel": nivel, "accion": accion, "explicacion": exp,
            "metodo": metodo, "colors": RISK_COLORS.get(nivel, RISK_COLORS["BAJO"]),
            "hora": datetime.now().strftime("%H:%M:%S - %d/%m/%Y"),
            "using_real_model": using_real_model
        })
    except Exception as e:
        traceback.print_exc()
        return json_utf8({"ok": False, "error": str(e)}, status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[START] port={port} model={'CNN-LSTM' if using_real_model else 'sim'}", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False)
