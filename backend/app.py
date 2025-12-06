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

# ---------------------------
# APP INIT
# ---------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# PATHS
# ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

DETECTOR_MODEL_PATH = os.path.join(MODEL_DIR, "xray_detector.h5")
CNN_MODEL_PATH       = os.path.join(MODEL_DIR, "fine_tuned_resnet.h5")
RF_PIPELINE_PATH     = os.path.join(MODEL_DIR, "rf_pipeline.pkl")

# ---------------------------
# LOAD MODELS
# ---------------------------
print("\n📌 Loading X-ray Detector...")
xray_detector = load_model(DETECTOR_MODEL_PATH)
print("✔ X-ray Detector Loaded")

print("\n📌 Loading Fracture CNN...")
cnn = load_model(CNN_MODEL_PATH)
print("✔ CNN Loaded")

print("\n📌 Loading RF Pipeline...")
pipe = joblib.load(RF_PIPELINE_PATH)
scaler = pipe["scaler"]
pca    = pipe["pca"]
rf     = pipe["rf"]
print("✔ Pipeline Loaded")

# Build 2048 feature extractor
feature_extractor = Model(
    inputs=cnn.input,
    outputs=cnn.get_layer("global_average_pooling2d").output
)
print("✔ Feature extractor ready")


# ---------------------------
# IMAGE PREPROCESSING (Detector)
# ---------------------------
def preprocess_detector(raw):
    arr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Invalid image")

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224))

    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, 0)
    return img


# ---------------------------
# IMAGE PREPROCESSING (Fracture Model)
# ---------------------------
def preprocess_fracture(raw):
    arr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise ValueError("Invalid image file")

    img = cv2.resize(img, (224, 224))
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, 0)
    return preprocess_input(img)


# ---------------------------
# PREDICT API
# ---------------------------
@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    raw = await file.read()

    # -----------------------------------------------------------
    # STEP 1 — DETECT IF IMAGE IS X-RAY
    # -----------------------------------------------------------
    img1 = preprocess_detector(raw)

    xray_prob = float(xray_detector.predict(img1)[0][0])
    print("🔍 X-ray Detector Prob:", xray_prob)

    if xray_prob < 0.5:
        return {
            "status": "not_xray",
            "prediction": "Not an X-ray Image",
            "confidence": xray_prob
        }

    # -----------------------------------------------------------
    # STEP 2 — FRACTURE CLASSIFICATION
    # -----------------------------------------------------------
    img2 = preprocess_fracture(raw)

    feat = feature_extractor.predict(img2)
    feat = feat.reshape(1, -1)

    scaled = scaler.transform(feat)
    reduced = pca.transform(scaled)

    pred = int(rf.predict(reduced)[0])
    prob = float(rf.predict_proba(reduced)[0].max())

    label_map = {0: "Normal", 1: "Fracture"}
    label = label_map[pred]

    return {
        "status": "success",
        "prediction": label,
        "confidence": prob
    }


@app.get("/")
def home():
    return {"message": "Backend is running"}
