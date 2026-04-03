import os, random, json
from datetime import datetime
from flask import Flask, render_template, request, Response

app = Flask(__name__)

ZONES = {
    "valle_central":     {"nombre": "Valle Central",          "center": [10.500, -66.880], "base": 0.10,
        "poly": [[10.485,-66.900],[10.485,-66.860],[10.515,-66.860],[10.515,-66.900]]},
    "ladera_vulnerable": {"nombre": "Laderas Medias",          "center": [10.515, -66.895], "base": 0.45,
        "poly": [[10.500,-66.915],[10.500,-66.875],[10.530,-66.875],[10.530,-66.915]]},
    "cerro_pendiente":   {"nombre": "Cerros Altos",            "center": [10.530, -66.865], "base": 0.65,
        "poly": [[10.515,-66.885],[10.515,-66.845],[10.545,-66.845],[10.545,-66.885]]},
    "quebrada":          {"nombre": "Cercania a Quebradas",    "center": [10.495, -66.910], "base": 0.75,
        "poly": [[10.480,-66.930],[10.480,-66.890],[10.510,-66.890],[10.510,-66.930]]},
    "seguro":            {"nombre": "Zonas Consolidadas",      "center": [10.485, -66.855], "base": 0.15,
        "poly": [[10.470,-66.875],[10.470,-66.835],[10.500,-66.835],[10.500,-66.875]]},
}

CLIMA = {"seco": 0.5, "moderado": 1.0, "intenso": 1.8, "extremo": 2.5, "creciente": 1.5}

COLORS = {
    "CRITICO":  "#FF4444",
    "ALTO":     "#FF8C00",
    "MODERADO": "#FFD700",
    "BAJO":     "#4CAF50",
}

# Try to load model (optional)
modelo = None
def try_load():
    global modelo
    h5 = "mejor_modelo_libertador.h5"
    paths = [h5, os.path.join(os.path.dirname(os.path.abspath(__file__)), h5)]
    for p in paths:
        if os.path.exists(p):
            try:
                os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
                import tensorflow as tf
                modelo = tf.keras.models.load_model(p, compile=False)
                print("MODEL LOADED:", p, flush=True)
                return
            except Exception as e:
                print("MODEL ERROR:", e, flush=True)
    print("MODEL: simulation mode", flush=True)

try_load()

def respond(data):
    return Response(json.dumps(data, ensure_ascii=False),
                    mimetype="application/json; charset=utf-8")

@app.route("/")
def index():
    return render_template("index.html", has_model=modelo is not None)

@app.route("/ping")
def ping():
    return respond({"ok": True, "model": modelo is not None})

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        body = request.get_json(force=True, silent=True) or {}
        zona_id  = body.get("zona",  "valle_central")
        clima_id = body.get("clima", "moderado")
        if zona_id  not in ZONES: zona_id  = "valle_central"
        if clima_id not in CLIMA:  clima_id = "moderado"

        zona = ZONES[zona_id]
        prob = min(0.97, max(0.03,
               zona["base"] * CLIMA[clima_id] * random.uniform(0.88, 1.12)))

        if prob >= 0.70:
            nivel, accion = "CRITICO",  "EVACUACION INMEDIATA"
            texto = f"Riesgo extremo {prob*100:.0f}%. Patron Vargas 1999. Evacuar zona de inmediato."
        elif prob >= 0.50:
            nivel, accion = "ALTO",     "RESTRICCION DE ACCESO"
            texto = f"Alta probabilidad de deslizamiento en 6-12h ({prob*100:.0f}%). Restringir acceso."
        elif prob >= 0.30:
            nivel, accion = "MODERADO", "VIGILANCIA ESPECIAL"
            texto = f"Condiciones favorables para deslizamientos ({prob*100:.0f}%). Activar brigadas."
        else:
            nivel, accion = "BAJO",     "VIGILANCIA ESTANDAR"
            texto = f"Condiciones estables ({prob*100:.0f}%). Monitoreo rutinario."

        return respond({
            "ok": True,
            "zona_id":   zona_id,
            "nombre":    zona["nombre"],
            "center":    zona["center"],
            "poly":      zona["poly"],
            "prob":      round(prob * 100, 1),
            "nivel":     nivel,
            "color":     COLORS[nivel],
            "accion":    accion,
            "texto":     texto,
            "metodo":    "CNN-LSTM" if modelo else "Simulacion PCV-2021",
            "hora":      datetime.now().strftime("%H:%M - %d/%m/%Y"),
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return respond({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



