from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import numpy as np
import cv2
import os
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.models import Model
import joblib

# ----------------------
# INITIALIZE APP
# ----------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------
# PATHS
# ----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

CNN_MODEL_PATH = os.path.join(MODEL_DIR, "fine_tuned_resnet.h5")
RF_PIPELINE_PATH = os.path.join(MODEL_DIR, "rf_pipeline.pkl")

# ----------------------
# LOAD MODELS
# ----------------------
cnn = None
feature_extractor = None
scaler = None
pca = None
rf = None

model_loaded = False
pipeline_loaded = False

print("Loading CNN model...")
try:
    cnn = load_model(CNN_MODEL_PATH)
    model_loaded = True
    print("Loaded:", CNN_MODEL_PATH)
except Exception as e:
    print("❌ Failed to load CNN:", e)

print("Loading RandomForest pipeline...")
try:
    pipe = joblib.load(RF_PIPELINE_PATH)
    scaler = pipe["scaler"]
    pca = pipe["pca"]
    rf = pipe["rf"]
    pipeline_loaded = True
    print("Loaded:", RF_PIPELINE_PATH)
except Exception as e:
    print("❌ Failed to load RF pipeline:", e)

# ----------------------
# BUILD 2048-DIM FEATURE EXTRACTOR
# ----------------------
if model_loaded:
    try:
        print("Building correct 2048-dim feature extractor...")
        feature_extractor = Model(
            inputs=cnn.input,
            outputs=cnn.get_layer("global_average_pooling2d").output
        )
        print("✔ Extractor ready. Output = 2048 dims")
    except Exception as e:
        print("❌ Failed to build feature extractor:", e)
        model_loaded = False

# ----------------------
# IMAGE PREPROCESSING
# ----------------------
def preprocess_image(raw):
    arr = np.asarray(bytearray(raw), dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise ValueError("Invalid image file.")

    img = cv2.resize(img, (224, 224))
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, 0)

    return preprocess_input(img)

# ----------------------
# PREDICT ENDPOINT
# ----------------------
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not model_loaded or not pipeline_loaded:
        return JSONResponse(
            {"status": "error", "message": "Model or pipeline not loaded."},
            status_code=503
        )

    try:
        raw = await file.read()
        img = preprocess_image(raw)

        # Extract CNN features (2048)
        feat = feature_extractor.predict(img)
        feat = feat.reshape(1, -1)

        # PCA + Scaling + RF prediction
        scaled = scaler.transform(feat)
        reduced = pca.transform(scaled)

        pred = int(rf.predict(reduced)[0])
        prob = float(rf.predict_proba(reduced)[0].max())

        # Map numeric → medical labels
        label_map = {
            0: "Normal",
            1: "Fracture"
        }
        label = label_map.get(pred, "Unknown")

        return {
            "status": "success",
            "prediction": label,
            "confidence": prob
        }

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/")
def home():
    return {"message": "Backend Running Successfully"}
