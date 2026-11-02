# 🚗 Driver Drowsiness Detection & Monitoring System

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.10-green.svg)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-orange.svg)](https://mediapipe.dev/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Random%20Forest-yellow.svg)](https://scikit-learn.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Dashboard-lightgrey.svg)](https://flask.palletsprojects.com/)

An AI-driven real-time Computer Vision and Machine Learning system that continuously monitors driver alertness via webcam. The system detects micro-sleeps, prolonged eye closure, and yawning using **MediaPipe Face Mesh (468 landmarks)** and a **Random Forest Classifier**, triggering instant audible warnings and logging incidents for road safety.

---

## 🌟 Key Features & Innovations

1. **🎯 Personalized Eye Calibration (5-Second Protocol)**
   - Solves the fixed threshold problem (where standard 0.21 EAR causes false alarms for drivers with naturally smaller or hooded eyes).
   - Computes personal baseline EAR and dynamically sets `personal_threshold = baseline_ear * 0.70` (clamped between 0.18 and 0.30).

2. **🚦 3-Level Risk Classification Engine**
   - **Level 1 (NORMAL):** Driver alert & eyes open.
   - **Level 2 (CAUTION):** Moderate signs of fatigue (yawning `MAR >= 0.62` or slow blinks).
   - **Level 3 (HIGH RISK):** Instant alert on sustained eye closure (`>= 0.5s`), triggering emergency audio alarm.

3. **🎵 Dual-Engine Song Alert (`funny_munni.mp3`)**
   - Employs **Pygame Mixer** on the local hardware speakers plus browser Web Audio, guaranteeing zero browser autoplay blocking.
   - Automatically stops playback the instant the driver opens their eyes (`< 0.4s`).

4. **🖥️ Modular Multi-Screen Cockpit Dashboard**
   - **Live Cockpit:** Real-time webcam feed with landmark HUD and risk badges.
   - **Calibration Studio:** Step-by-step visual baseline gauge.
   - **AI Lab & Simulator:** Interactive "What-If" sliders testing the Random Forest model live with confidence scores.
   - **Live Telemetry:** Streaming line charts for EAR and MAR.
   - **Incident Logs & Audit:** Filterable safety log table with CSV export.
   - **Viva & Architecture:** Complete 6-step system pipeline & model defense Q&As.

5. **📓 Enhanced Jupyter Notebook**
   - Includes full pipeline with step-by-step Hinglish explanations, fixed `closed_seconds` reference, and 3-level detection.

---

## 📁 Repository Structure

```text
├── app.py                                   # Flask Backend & Detection Engine
├── Driver_Drowsiness_Detection_Jupyter.ipynb # Complete Jupyter Notebook Pipeline
├── requirements.txt                         # Project Dependencies
├── run_dashboard.bat                        # 1-Click launcher for Web Dashboard
├── run_notebook.bat                         # 1-Click launcher for Jupyter Notebook
├── README.md                                # Project Documentation
├── templates/
│   └── index.html                           # Multi-Screen Dashboard SPA
├── static/
│   ├── css/style.css                        # Modern EV Cockpit Dark Theme
│   ├── js/dashboard.js                      # Navigation, Real-Time Polling & Charts
│   └── sounds/                              # Audio directory (place funny_munni.mp3 here)
├── models/
│   ├── drowsiness_model.joblib              # Trained Random Forest Model
│   └── face_landmarker.task                 # MediaPipe Model Weights
├── data/
│   └── features.csv                         # Custom Empirical Dataset (2,181 frames)
└── logs/
    └── drowsiness_events.csv                # Timestamped Incident History
```

---

## 🛠️ Technology Stack

- **Core Runtime:** Python 3.11
- **Computer Vision:** OpenCV, MediaPipe Face Mesh (468 landmarks)
- **Machine Learning:** Scikit-Learn (Random Forest: 200 trees, balanced weights)
- **Audio Output:** Pygame Mixer (`funny_munni.mp3`)
- **Web Dashboard:** Flask, HTML5, CSS3, JavaScript, Chart.js

---

## 🚀 Quick Start Guide

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/krishnasingh95/driver-drowsiness-detection.git
cd driver-drowsiness-detection

# Create and activate virtual environment (or use Conda)
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Audio Setup
Place your alert audio track (e.g., `funny_munni.mp3` or any custom audio) in the project root and in `static/sounds/alert.mp3`.

### 3. Run Web Dashboard

**Option A (Windows 1-Click):** Double-click `run_dashboard.bat`  
**Option B (Terminal):**
```bash
python app.py
```
Open **`http://localhost:5000`** in your web browser.

### 4. Run Jupyter Notebook

```bash
jupyter notebook Driver_Drowsiness_Detection_Jupyter.ipynb
```

---

## 📊 Dataset & Model Evaluation

- **Total Samples:** 2,181 annotated frames
  - **Alert:** 1,191 frames (54.6%)
  - **Drowsy:** 990 frames (45.4%)
- **Feature Set:** `left_ear`, `right_ear`, `avg_ear`, `mar`, `eye_closed_seconds`
- **Validation Accuracy:** **89.7%**
- **Drowsy Precision:** **92.0%**
- **Drowsy Recall:** **84.0%**

---

## 👥 Team & College Details

**Bansal Institute of Engineering and Technology, Lucknow**  
Department of Artificial Intelligence and Machine Learning (AIML)  
Academic Session: 2026–2027  

- **Krishna Singh**
- **Vikash Gupta**
- **Ateek Ahmad**

---

## ⚠️ Academic Disclaimer

This project is an academic prototype developed for educational and experimental evaluation. It is not certified for commercial vehicle safety deployment.
