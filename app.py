"""
Driver Drowsiness Detection and Monitoring System
Advanced Flask Web Application with Multi-Screen Dashboard & Dual Audio Engine
Author: B.Tech AI/ML | Mini Project 2024-25
"""

import os
import sys
import time
import csv
import json
import base64
import threading
from datetime import datetime

import cv2
import numpy as np
import pandas as pd
import joblib
import mediapipe as mp
import pygame
from flask import Flask, render_template, Response, jsonify, request, stream_with_context, send_file
from flask_cors import CORS

# ─────────────────────────────────────────────
#  FLASK INITIALIZATION
# ─────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
#  DIRECTORIES & FILE PATHS
# ─────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH    = os.path.join(BASE_DIR, "models", "drowsiness_model.joblib")
DATA_PATH     = os.path.join(BASE_DIR, "data",   "features.csv")
LOG_PATH      = os.path.join(BASE_DIR, "logs",   "drowsiness_events.csv")
AUDIO_PATH    = os.path.join(BASE_DIR, "static", "sounds", "alert.mp3")

# ─────────────────────────────────────────────
#  PYGAME HARDWARE AUDIO ENGINE (Laptop Speakers)
# ─────────────────────────────────────────────
audio_enabled = True
audio_playing = False
audio_lock    = threading.Lock()

try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    if os.path.exists(AUDIO_PATH):
        pygame.mixer.music.load(AUDIO_PATH)
        print(f"[AUDIO] Pygame loaded alert sound: {AUDIO_PATH}")
    else:
        print(f"[AUDIO WARN] Audio file not found at {AUDIO_PATH}")
except Exception as e:
    print(f"[AUDIO ERROR] Pygame init failed: {e}")

def play_hardware_sound():
    """Play funny_munni.mp3 directly through laptop speakers via Pygame in a loop."""
    global audio_playing
    if not audio_enabled:
        return
    with audio_lock:
        try:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)
                audio_playing = True
        except Exception as e:
            print(f"[AUDIO PLAY ERROR] {e}")

def stop_hardware_sound():
    """Stop Pygame music playback."""
    global audio_playing
    with audio_lock:
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            audio_playing = False
        except Exception as e:
            print(f"[AUDIO STOP ERROR] {e}")

# ─────────────────────────────────────────────
#  MEDIAPIPE FACE MESH SETUP
# ─────────────────────────────────────────────
mp_face_mesh = mp.solutions.face_mesh
face_mesh    = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

LEFT_EYE_INDICES  = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_INDICES = [33,  160, 158, 133, 153, 144]
MOUTH_INDICES     = [61,  291, 39,  181, 0,   17,  269, 405]

# ─────────────────────────────────────────────
#  LOAD MACHINE LEARNING MODEL
# ─────────────────────────────────────────────
model        = None
feature_cols = ["left_ear", "right_ear", "avg_ear", "mar", "eye_closed_seconds"]

if os.path.exists(MODEL_PATH):
    try:
        bundle = joblib.load(MODEL_PATH)
        if isinstance(bundle, dict):
            model        = bundle.get("model")
            feature_cols = bundle.get("feature_columns", feature_cols)
        else:
            model = bundle
        print(f"[ML] Random Forest loaded: {type(model).__name__} | Classes: {list(getattr(model, 'classes_', []))}")
    except Exception as e:
        print(f"[ML WARN] Could not load model: {e}")
else:
    print(f"[ML WARN] Model not found at {MODEL_PATH}")

# ─────────────────────────────────────────────
#  SHARED SYSTEM STATE
# ─────────────────────────────────────────────
state_lock = threading.Lock()
alarm_trigger_delay = 0.5  # Instant song trigger as soon as eyes close (0.5 seconds)

state = {
    # Biometric Telemetry
    "left_ear":           0.0,
    "right_ear":          0.0,
    "avg_ear":            0.0,
    "mar":                0.0,
    "eye_closed_seconds": 0.0,

    # 3-Level Risk Classification ("NORMAL", "CAUTION", "HIGH_RISK")
    "risk_level":         "NORMAL",

    # Machine Learning Output
    "ml_prediction":      "Alert",
    "ml_confidence":      0.0,

    # Personalized Calibration
    "calibrated":         False,
    "calibration_progress": 0,
    "baseline_ear":       0.0,
    "personal_threshold": 0.25,

    # Alarm sensitivity settings
    "alarm_delay":        0.5,

    # Diagnostics
    "face_detected":      False,
    "fps":                0.0,
    "play_alert":         False,
    "audio_playing":      False,
    "audio_enabled":      True,

    # Session Analytics
    "total_alerts":       0,
    "session_start":      time.time(),
}

# ─────────────────────────────────────────────
#  BIOMETRIC CALCULATIONS (EAR & MAR)
# ─────────────────────────────────────────────
def calculate_ear(landmarks, eye_indices, w, h):
    pts = np.array([[landmarks[i].x * w, landmarks[i].y * h] for i in eye_indices])
    A = np.linalg.norm(pts[1] - pts[5])
    B = np.linalg.norm(pts[2] - pts[4])
    C = np.linalg.norm(pts[0] - pts[3])
    return float((A + B) / (2.0 * C + 1e-6))

def calculate_mar(landmarks, mouth_indices, w, h):
    pts = np.array([[landmarks[i].x * w, landmarks[i].y * h] for i in mouth_indices])
    A = np.linalg.norm(pts[2] - pts[6])
    B = np.linalg.norm(pts[3] - pts[5])
    C = np.linalg.norm(pts[0] - pts[1])
    return float((A + B) / (2.0 * C + 1e-6))

def log_event(event_type, ml_pred, ear_val, mar_val, closed_sec):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    write_header = not os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "event_type", "ml_prediction", "avg_ear", "mar", "eye_closed_seconds"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            event_type,
            ml_pred,
            f"{ear_val:.3f}",
            f"{mar_val:.3f}",
            f"{closed_sec:.1f}"
        ])

# ─────────────────────────────────────────────
#  VIDEO DRAWING & HUD OVERLAY
# ─────────────────────────────────────────────
def draw_overlay(frame, s):
    h, w = frame.shape[:2]
    risk_colors = {
        "NORMAL":    (0, 200, 80),    # Green
        "CAUTION":   (0, 165, 255),   # Amber/Orange
        "HIGH_RISK": (0, 0, 240),     # Red
    }
    color = risk_colors.get(s["risk_level"], (255, 255, 255))

    # Top status banner
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 55), (15, 18, 25), -1)
    frame = cv2.addWeighted(overlay, 0.75, frame, 0.25, 0)

    # Risk badge
    badge_label = s["risk_level"].replace("_", " ")
    cv2.rectangle(frame, (10, 8), (180, 48), color, -1)
    cv2.putText(frame, badge_label, (18, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Audio playing indicator
    if s["play_alert"]:
        cv2.putText(frame, "SONG ALERT ACTIVE", (195, 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

    # FPS
    cv2.putText(frame, f"FPS: {s['fps']:.1f}", (w - 110, 36),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    # Bottom telemetry bar
    cv2.rectangle(frame, (0, h - 38), (w, h), (15, 18, 25), -1)
    hud_text = (
        f"EAR: {s['avg_ear']:.3f} | MAR: {s['mar']:.3f} | "
        f"Closed: {s['eye_closed_seconds']:.1f}s | "
        f"ML: {s['ml_prediction']} ({int(s['ml_confidence']*100)}%)"
    )
    cv2.putText(frame, hud_text, (12, h - 14),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)

    # Calibration Banner if in progress
    if not s["calibrated"]:
        prog = s["calibration_progress"]
        cv2.rectangle(frame, (0, 56), (w, 88), (25, 30, 45), -1)
        prog_w = int(w * prog / 100)
        cv2.rectangle(frame, (0, 56), (prog_w, 88), (0, 180, 70), -1)
        cv2.putText(frame, f"Calibrating Eyes: {prog}% (Keep looking naturally at screen)",
                    (15, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

    if not s["face_detected"]:
        cv2.putText(frame, "NO FACE DETECTED", (w // 2 - 130, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 100, 255), 2)

    return frame

# ─────────────────────────────────────────────
#  CAMERA CAPTURE & THREADING ENGINE
# ─────────────────────────────────────────────
class VideoCamera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.running = True
        self.frame = None
        self.lock = threading.Lock()

        # Timing
        self._prev_time = time.time()
        self._eye_close_start = None
        self._last_drowsy_time = 0.0

        # Calibration
        self._cal_ears = []
        self._cal_start = time.time()
        self._cal_duration = 5.0
        self._calibrated = False

        # Alert logging
        self._alert_logged = False

        # Background thread
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self):
        while self.running:
            ret, raw = self.cap.read()
            if not ret:
                time.sleep(0.04)
                continue

            frame = cv2.flip(raw, 1)
            now = time.time()
            h, w = frame.shape[:2]

            fps = 1.0 / max(now - self._prev_time, 1e-6)
            self._prev_time = now

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = face_mesh.process(rgb)

            left_ear = right_ear = avg_ear = mar = 0.0
            closed_secs = 0.0
            face_found = False
            risk = "NORMAL"
            ml_pred = "Alert"
            ml_conf = 0.0
            play_alert = False

            if res.multi_face_landmarks:
                face_found = True
                lm = res.multi_face_landmarks[0].landmark

                left_ear  = calculate_ear(lm, LEFT_EYE_INDICES, w, h)
                right_ear = calculate_ear(lm, RIGHT_EYE_INDICES, w, h)
                avg_ear   = (left_ear + right_ear) / 2.0
                mar       = calculate_mar(lm, MOUTH_INDICES, w, h)

                # ── 1. PERSONALIZED CALIBRATION ─────────────────────
                if not self._calibrated:
                    elapsed = now - self._cal_start
                    prog = min(int(elapsed / self._cal_duration * 100), 99)
                    self._cal_ears.append(avg_ear)

                    if elapsed >= self._cal_duration and len(self._cal_ears) > 10:
                        baseline = float(np.percentile(self._cal_ears, 80))
                        personal = float(np.clip(baseline * 0.70, 0.18, 0.30))
                        self._calibrated = True
                        prog = 100
                        with state_lock:
                            state["calibrated"]           = True
                            state["baseline_ear"]         = round(baseline, 3)
                            state["personal_threshold"]   = round(personal, 3)
                            state["calibration_progress"] = 100
                    else:
                        with state_lock:
                            state["calibration_progress"] = prog

                # ── 2. DETECTION PHASE ──────────────────────────────
                with state_lock:
                    threshold = state["personal_threshold"]

                # Eye closure duration calculation
                if avg_ear < threshold:
                    if self._eye_close_start is None:
                        self._eye_close_start = now
                    closed_secs = now - self._eye_close_start
                else:
                    self._eye_close_start = None
                    closed_secs = 0.0
                    self._alert_logged = False

                # Random Forest ML Inference
                if model is not None:
                    features = np.array([[left_ear, right_ear, avg_ear, mar, closed_secs]])
                    raw_pred = model.predict(features)[0]
                    proba    = model.predict_proba(features)[0]
                    classes  = list(model.classes_)
                    ml_pred  = str(raw_pred)
                    pred_idx = classes.index(ml_pred) if ml_pred in classes else 0
                    ml_conf  = float(proba[pred_idx])
                else:
                    ml_pred = "Drowsy" if avg_ear < threshold else "Alert"
                    ml_conf = 0.88

                # ── 3. THREE-LEVEL RISK CLASSIFICATION & INSTANT SONG ALERT ──
                # Jaise hi aankh band ho (closed_secs >= alarm_trigger_delay), song turant baje!
                with state_lock:
                    delay = state.get("alarm_delay", 0.5)

                is_eyes_closed = (avg_ear < threshold and closed_secs >= delay)
                is_ml_drowsy_closed = (ml_pred == "Drowsy" and closed_secs >= 0.3)

                # Level 3: HIGH RISK (Song plays immediately when eyes are closed!)
                if is_eyes_closed or is_ml_drowsy_closed or (closed_secs >= delay):
                    risk = "HIGH_RISK"
                    play_alert = True
                    self._last_drowsy_time = now

                    # Play funny_munni.mp3 song via Pygame on laptop speakers immediately
                    play_hardware_sound()

                    if not self._alert_logged:
                        log_event("EYES_CLOSED_WARNING", ml_pred, avg_ear, mar, closed_secs)
                        with state_lock:
                            state["total_alerts"] += 1
                        self._alert_logged = True

                # Level 2: CAUTION (Yawning or partial eye squint)
                elif (mar >= 0.62) or (closed_secs >= 0.2):
                    risk = "CAUTION"
                    play_alert = False
                    if (now - self._last_drowsy_time) >= 0.4:
                        stop_hardware_sound()

                # Level 1: NORMAL (Eyes open & attentive)
                else:
                    risk = "NORMAL"
                    play_alert = False
                    if (now - self._last_drowsy_time) >= 0.4:
                        stop_hardware_sound()

                # Draw facial landmark points
                for idx in LEFT_EYE_INDICES + RIGHT_EYE_INDICES:
                    pt = lm[idx]
                    cv2.circle(frame, (int(pt.x * w), int(pt.y * h)), 2, (0, 255, 0), -1)
                for idx in MOUTH_INDICES:
                    pt = lm[idx]
                    cv2.circle(frame, (int(pt.x * w), int(pt.y * h)), 2, (0, 165, 255), -1)

            else:
                self._eye_close_start = None
                stop_hardware_sound()

            # Update thread-safe snapshot
            with state_lock:
                state.update({
                    "left_ear":           round(left_ear, 3),
                    "right_ear":          round(right_ear, 3),
                    "avg_ear":            round(avg_ear, 3),
                    "mar":                round(mar, 3),
                    "eye_closed_seconds": round(closed_secs, 2),
                    "risk_level":         risk,
                    "ml_prediction":      ml_pred,
                    "ml_confidence":      round(ml_conf, 3),
                    "face_detected":      face_found,
                    "fps":                round(fps, 1),
                    "play_alert":         play_alert,
                    "audio_playing":      audio_playing,
                    "audio_enabled":      audio_enabled,
                })

            frame = draw_overlay(frame, {**state})

            with self.lock:
                self.frame = frame

    def get_frame(self):
        with self.lock:
            return self.frame

    def release(self):
        self.running = False
        stop_hardware_sound()
        self.cap.release()

camera = None

def get_camera():
    global camera
    if camera is None or not camera.running:
        camera = VideoCamera()
    return camera

def gen_frames():
    cam = get_camera()
    while True:
        frame = cam.get_frame()
        if frame is None:
            time.sleep(0.03)
            continue
        ret, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
        time.sleep(0.033)

# ─────────────────────────────────────────────
#  FLASK ROUTES & REST APIS
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    get_camera()
    return Response(stream_with_context(gen_frames()), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/api/state")
def api_state():
    with state_lock:
        snap = dict(state)
    snap["session_duration"] = round(time.time() - snap["session_start"], 1)
    return jsonify(snap)

@app.route("/api/reset_calibration", methods=["POST"])
def reset_calibration():
    global camera
    if camera:
        camera.release()
        camera = None
    with state_lock:
        state["calibrated"]           = False
        state["calibration_progress"] = 0
        state["personal_threshold"]   = 0.25
        state["baseline_ear"]         = 0.0
    get_camera()
    return jsonify({"status": "ok", "message": "Calibration restarted."})

@app.route("/api/set_alarm_delay", methods=["POST"])
def set_alarm_delay():
    data = request.json or {}
    new_delay = float(data.get("alarm_delay", 0.5))
    new_delay = max(0.2, min(new_delay, 3.0))
    with state_lock:
        state["alarm_delay"] = round(new_delay, 2)
    return jsonify({"status": "ok", "alarm_delay": state["alarm_delay"]})

@app.route("/api/test_sound_on", methods=["POST"])
def test_sound_on():
    play_hardware_sound()
    with state_lock:
        state["play_alert"] = True
    return jsonify({"status": "playing", "message": "Alert song playing"})

@app.route("/api/test_sound_off", methods=["POST"])
def test_sound_off():
    stop_hardware_sound()
    with state_lock:
        state["play_alert"] = False
    return jsonify({"status": "stopped", "message": "Alert song stopped"})

@app.route("/api/toggle_audio", methods=["POST"])
def toggle_audio():
    global audio_enabled
    audio_enabled = not audio_enabled
    if not audio_enabled:
        stop_hardware_sound()
    with state_lock:
        state["audio_enabled"] = audio_enabled
    return jsonify({"audio_enabled": audio_enabled})

@app.route("/api/simulate_predict", methods=["POST"])
def simulate_predict():
    """Allows user to simulate custom EAR/MAR/Closed seconds in the ML Lab."""
    data = request.json or {}
    l_ear  = float(data.get("left_ear", 0.35))
    r_ear  = float(data.get("right_ear", 0.35))
    avg_e  = (l_ear + r_ear) / 2.0
    mar_v  = float(data.get("mar", 0.05))
    closed = float(data.get("eye_closed_seconds", 0.0))
    thresh = float(data.get("threshold", 0.25))

    ml_p = "Alert"
    ml_c = 0.5
    if model is not None:
        feats = np.array([[l_ear, r_ear, avg_e, mar_v, closed]])
        raw   = model.predict(feats)[0]
        prob  = model.predict_proba(feats)[0]
        cl    = list(model.classes_)
        ml_p  = str(raw)
        idx   = cl.index(ml_p) if ml_p in cl else 0
        ml_c  = float(prob[idx])

    # 3-level simulation (eyes closed >= 0.5s triggers HIGH RISK & Song!)
    if closed >= 0.5 or (ml_p == "Drowsy" and closed >= 0.3):
        sim_risk = "HIGH_RISK"
    elif mar_v >= 0.62 or closed >= 0.2:
        sim_risk = "CAUTION"
    else:
        sim_risk = "NORMAL"

    return jsonify({
        "ml_prediction": ml_p,
        "ml_confidence": round(ml_c, 3),
        "risk_level": sim_risk,
        "avg_ear": round(avg_e, 3),
    })

@app.route("/api/logs")
def api_logs():
    events = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, newline="") as f:
            reader = csv.DictReader(f)
            events = list(reader)[-60:]
    return jsonify(events)

@app.route("/api/clear_logs", methods=["POST"])
def api_clear_logs():
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "event_type", "ml_prediction", "avg_ear", "mar", "eye_closed_seconds"])
    with state_lock:
        state["total_alerts"] = 0
    return jsonify({"status": "cleared"})

@app.route("/api/download_logs")
def api_download_logs():
    if os.path.exists(LOG_PATH):
        return send_file(LOG_PATH, as_attachment=True, download_name="drowsiness_events.csv")
    return jsonify({"error": "No log file found"}), 404

@app.route("/api/stats")
def api_stats():
    with state_lock:
        total_alerts  = state["total_alerts"]
        session_start = state["session_start"]
    dataset_rows = 0
    if os.path.exists(DATA_PATH):
        try:
            df = pd.read_csv(DATA_PATH)
            dataset_rows = len(df)
        except Exception:
            pass

    importances = []
    if model is not None and hasattr(model, "feature_importances_"):
        for f, imp in zip(feature_cols, model.feature_importances_):
            importances.append({"feature": f, "importance": round(float(imp), 4)})
        importances.sort(key=lambda x: x["importance"], reverse=True)

    return jsonify({
        "total_alerts":       total_alerts,
        "session_duration":   round(time.time() - session_start, 1),
        "model_loaded":       model is not None,
        "model_type":         type(model).__name__ if model else "None",
        "classes":            list(getattr(model, "classes_", [])),
        "features":           feature_cols,
        "dataset_rows":       dataset_rows,
        "feature_importance": importances,
    })

@app.route("/stop_camera", methods=["POST"])
def stop_camera():
    global camera
    if camera:
        camera.release()
        camera = None
    return jsonify({"status": "stopped"})

# ─────────────────────────────────────────────
#  APP ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  [SYSTEM] DRIVER DROWSINESS DETECTION & MONITORING SYSTEM")
    print("  Web Dashboard: http://localhost:5000")
    print("  Hardware Audio: funny_munni.mp3 ready")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
