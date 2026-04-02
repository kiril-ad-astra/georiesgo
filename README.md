# GeoRiesgo Caracas – Sistema de Alerta Temprana 🗺️

App web Flask para análisis de riesgo de deslizamientos en el Municipio Libertador, Caracas.

## Estructura del proyecto

```
georiesgo/
├── app.py                  ← Backend Flask + lógica del modelo
├── requirements.txt        ← Dependencias Python
├── Procfile                ← Comando de inicio (Heroku / Railway / Render)
├── runtime.txt             ← Versión de Python
├── railway.json            ← Config Railway
├── render.yaml             ← Config Render
├── templates/
│   └── index.html          ← Frontend principal
└── static/
    ├── css/style.css       ← Estilos dashboard
    └── js/app.js           ← Lógica mapa Leaflet + llamadas API
```

---

## 🚀 Despliegue en Railway (recomendado, GRATIS)

### Paso 1 – Preparar repositorio GitHub

```bash
cd georiesgo
git init
git add .
git commit -m "GeoRiesgo Caracas v3.2"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/georiesgo-caracas.git
git push -u origin main
```

### Paso 2 – Crear proyecto en Railway

1. Ve a https://railway.app y crea cuenta (gratis con GitHub)
2. Clic en **New Project → Deploy from GitHub repo**
3. Selecciona el repositorio `georiesgo-caracas`
4. Railway detecta el `Procfile` automáticamente → **Deploy**

### Paso 3 – Obtener URL de Railway

- Railway te da una URL como: `https://georiesgo-caracas-production.up.railway.app`

### Paso 4 – Conectar dominio yoli-test.work.gd

1. En Railway → tu proyecto → **Settings → Domains → Custom Domain**
2. Escribe: `yoli-test.work.gd` → clic **Add**
3. Railway te muestra un registro DNS (CNAME)

#### En tu proveedor DNS (donde registraste work.gd):

| Tipo  | Nombre            | Valor                                          |
|-------|-------------------|------------------------------------------------|
| CNAME | yoli-test         | `georiesgo-caracas-production.up.railway.app`  |

4. Espera 5-30 minutos para propagación DNS
5. ✅ Tu app estará en `https://yoli-test.work.gd`

---

## 🚀 Despliegue en Render (alternativa gratis)

1. Ve a https://render.com → **New Web Service**
2. Conecta tu repositorio GitHub
3. Render detecta `render.yaml` automáticamente
4. Clic **Create Web Service**
5. URL: `https://georiesgo-caracas.onrender.com`

Para conectar el dominio: **Settings → Custom Domains → Add Custom Domain**

---

## 🤖 Agregar el modelo CNN-LSTM real

Si tienes el archivo `mejor_modelo_libertador.h5`:

1. Añádelo a la raíz del proyecto
2. Agrega a `requirements.txt`:
   ```
   tensorflow==2.16.1
   ```
3. Sube los cambios:
   ```bash
   git add mejor_modelo_libertador.h5 requirements.txt
   git commit -m "Añadir modelo CNN-LSTM"
   git push
   ```
4. Railway/Render redesplegará automáticamente
5. La app detectará el modelo y mostrará **"CNN-LSTM ACTIVO"**

> ⚠️ Nota: El modelo .h5 puede ser grande. Si supera 100 MB, usa Git LFS:
> ```bash
> git lfs track "*.h5"
> git add .gitattributes
> ```

---

## 🖥️ Ejecutar localmente

```bash
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

---

## Variables de entorno (opcionales)

| Variable | Descripción             | Default |
|----------|-------------------------|---------|
| `PORT`   | Puerto del servidor     | 5000    |

---

## Stack tecnológico

- **Backend**: Flask + Gunicorn + NumPy
- **Frontend**: HTML/CSS/JS vanilla + Leaflet.js (OpenStreetMap)
- **Mapa**: CartoDB Dark tiles (sin API key requerida)
- **Modelo (opcional)**: TensorFlow/Keras CNN-LSTM

---

© 2026 UNES · Datos: INAMEH · FUNVISIS · IMME-UCV
