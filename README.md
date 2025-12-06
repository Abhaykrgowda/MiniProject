# M_P Integration - AI-Powered X-Ray Fracture Detection

A full-stack web application for detecting bone fractures in X-Ray images using a fine-tuned ResNet CNN model combined with a Random Forest classifier for enhanced predictions.

## Project Structure

```
M_P_Integration/
├── backend/
│   ├── app.py                      # FastAPI application with /predict endpoint
│   ├── requirements.txt            # Python dependencies
│   ├── models/                     # Model storage (create this folder)
│   │   ├── fine_tuned_resnet.h5   # Keras CNN model
│   │   └── rf_pipeline.pkl        # Sklearn Random Forest pipeline
│   └── __init__.py
│
├── frontend/
│   ├── index.html                  # Main HTML UI
│   ├── app.js                      # Upload & prediction logic
│   ├── styles.css                  # Styling
│   └── src/
│       └── app.js                  # Organized copy of app.js
│
├── README.md                        # This file
└── .gitignore
```

## Features

- **Drag & Drop Upload**: Simple drag-and-drop interface for X-Ray images
- **Patient Information**: Track patient name with each analysis
- **AI Prediction**: Uses fine-tuned ResNet50 for feature extraction + Random Forest for classification
- **Confidence Score**: Returns prediction confidence percentage
- **CORS Enabled**: Frontend and backend can run on different machines/ports
- **Error Handling**: Clear error messages and diagnostics for troubleshooting

## Requirements

### Backend
- Python 3.8+
- FastAPI
- TensorFlow (with Keras)
- scikit-learn
- OpenCV (cv2)
- joblib
- numpy

### Frontend
- Modern browser (Chrome, Firefox, Safari, Edge)
- Node.js (optional, for local static server)

## Setup

### 1. Backend Setup

1. **Create Python virtual environment**:
   ```powershell
   cd C:\M_P_Integration\backend
   python -m venv .venv
   .\\.venv\\Scripts\\Activate.ps1
   ```

2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Create models directory and upload model files**:
   ```powershell
   mkdir models
   # Copy fine_tuned_resnet.h5 to backend/models/
   # Copy rf_pipeline.pkl to backend/models/
   ```

4. **Verify models are loaded correctly**:
   - Models should be placed at:
     - `C:\M_P_Integration\backend\models\fine_tuned_resnet.h5`
     - `C:\M_P_Integration\backend\models\rf_pipeline.pkl`

### 2. Frontend Setup

No special setup required if serving static files. The frontend is plain HTML/CSS/JavaScript.

## Running the Application

### Option A: Run from Project Root

**Backend (FastAPI/Uvicorn)**:
```powershell
cd C:\M_P_Integration
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend (Static Server)** - in another terminal:
```powershell
cd C:\M_P_Integration\frontend
npx http-server -p 8080
# or use Python:
python -m http.server 8080
# or Node (requires serve package):
npx serve -l 8080
```

### Option B: Run Backend from Backend Folder

```powershell
cd C:\M_P_Integration\backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Access the Application

1. Backend API: `http://<your-ip>:8000`
   - Health check: `GET http://<your-ip>:8000/`
   - Prediction: `POST http://<your-ip>:8000/predict` (multipart/form-data with `file` field)

2. Frontend UI: `http://<your-ip>:8080`
   - Upload X-Ray image
   - View prediction and confidence

## API Endpoints

### GET /
Returns backend health status.
```json
{"msg": "Backend Running"}
```

### POST /predict
Accepts an X-Ray image and returns fracture prediction.

**Request**:
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (image file)

**Response** (Success - 200):
```json
{
  "status": "success",
  "prediction": 1,
  "confidence": 0.95
}
```

**Response** (Models Not Loaded - 503):
```json
{
  "status": "error",
  "message": "Model or pipeline not loaded on server."
}
```

**Response** (Error - 500):
```json
{
  "status": "error",
  "message": "<error details>"
}
```

## Configuration

### Backend URL from Frontend
By default, the frontend automatically detects the backend URL using the current page's hostname:
- Page at `http://10.155.237.174:8080` → Backend URL: `http://10.155.237.174:8000`

**To override**, add this to your HTML before `<script src="app.js"></script>`:
```html
<script>
  window.BACKEND_URL = "http://your-backend-ip:8000";
</script>
```

## Troubleshooting

### "Upload failed" Alert
1. **Check browser console** (F12 → Console tab):
   - Look for "Using BACKEND_URL: ..." log
   - Check for error messages (network, CORS, etc.)

2. **Check backend is running**:
   ```powershell
   # From any machine that can reach the backend host
   Invoke-RestMethod -Uri 'http://<backend-ip>:8000/'
   # Should return: @{msg=Backend Running}
   ```

3. **Check models are loaded**:
   - Backend terminal shows startup logs
   - If you see "Failed to load CNN model" or "Failed to load RF pipeline", ensure models exist in `backend/models/`

4. **Network connectivity**:
   ```powershell
   Test-NetConnection -ComputerName <backend-ip> -Port 8000
   ```
   - If fails, check firewall and network settings

5. **Browser DevTools Network tab**:
   - Inspect `/predict` request
   - Check Status code (503 = models missing, 422 = form field mismatch, 500 = server error)
   - Read Response body for error details

### Model Files Missing
- Error: `"Model or pipeline not loaded on server." (503)`
- Solution: Copy model files to `C:\M_P_Integration\backend\models\`
  - `fine_tuned_resnet.h5` (CNN model)
  - `rf_pipeline.pkl` (RF pipeline with scaler & PCA)

### Port Already in Use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000
# Kill the process (replace PID with the actual process ID)
taskkill /PID <PID> /F
```

### CORS Errors
- Backend has `allow_origins=["*"]`, so CORS should not be the issue
- If you see CORS errors, check browser console for exact error details

## Development Notes

### Image Preprocessing
The backend expects:
- Image format: JPEG, PNG, or other standard formats
- Size: Automatically resized to 224×224 for CNN
- Color: Converted to RGB (from grayscale or color)
- Normalization: Pixel values normalized to [0, 1]

### Model Pipeline
1. **CNN Feature Extraction**: ResNet50 (pre-trained, fine-tuned) extracts features
2. **Scaling**: StandardScaler normalizes features
3. **Dimensionality Reduction**: PCA reduces dimensionality
4. **Classification**: Random Forest predicts fracture presence/type

### Frontend Customization
- Edit `styles.css` for UI appearance
- Edit `app.js` for upload logic
- Edit `index.html` for layout

## Dependencies

See `backend/requirements.txt` for exact versions. Key packages:
- fastapi
- uvicorn
- tensorflow
- scikit-learn
- opencv-python
- pillow
- numpy
- joblib

## License

This project is for educational and research purposes.

## Support

For issues or questions:
1. Check browser console (F12)
2. Check backend terminal logs
3. Review the Troubleshooting section above
4. Verify model files are in `backend/models/`
