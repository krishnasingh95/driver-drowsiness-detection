# Driver Drowsiness Detection System

## Project Overview

The Driver Drowsiness Detection System is a Python-based mini project that uses computer vision and machine learning to identify possible signs of driver drowsiness through a webcam.

When drowsiness is detected, the system displays a warning and can play an audio song as an alert.

## Objectives

* Detect facial landmarks using MediaPipe.
* Calculate Eye Aspect Ratio (EAR) and Mouth Aspect Ratio (MAR).
* Classify facial features using a Random Forest model.
* Display real-time Alert or Drowsy status.
* Play an audio alert when drowsiness is detected.
* Record drowsiness events with timestamps.

## Technologies Used

* Python 3.11
* OpenCV
* MediaPipe
* NumPy
* Pandas
* Scikit-learn
* Random Forest Classifier
* Pygame
* Jupyter Notebook

## Project Structure

```text
Mini Project/
├── Driver_Drowsiness_Detection_Jupyter.ipynb
├── funny_munni.mp3
├── requirements.txt
├── README.md
├── data/
│   └── features.csv
├── models/
│   └── drowsiness_model.joblib
└── logs/
    └── drowsiness_events.csv
```

The dataset, trained model, and event log should be present in their respective folders. The exact files may vary depending on your project setup.

## Installation

1. Install Python 3.11.

2. Open a terminal in the project folder.

3. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

4. Activate it on Windows:

   ```bash
   .venv\Scripts\activate
   ```

5. Install the required packages:

   ```bash
   python -m pip install -r requirements.txt
   ```

## How to Run

1. Open the project folder.

2. Start Jupyter Notebook:

   ```bash
   python -m notebook
   ```

3. Open `Driver_Drowsiness_Detection_Jupyter.ipynb`.

4. Select the Python environment that has the project dependencies installed.

5. Run the notebook cells in order.

6. Ensure that the trained model and audio file are available at the paths expected by the notebook.

7. Run the real-time detection function to start webcam monitoring.

8. Press `Q` in the webcam window to stop detection.

## Model Evaluation

In the initial test, the Random Forest model achieved approximately **80.8% test accuracy** on the collected dataset.

This result reflects the project's initial test split and does not establish reliability under real driving conditions.

## Limitations

* Performance may vary with lighting, camera angle, glasses, and different people.
* Eye closure or yawning alone does not prove that a driver is dangerously sleepy.
* False positive and false negative predictions are possible.
* More diverse data and independent testing are needed to improve evaluation.

## Future Scope

* Collect data from more people and varied conditions.
* Improve warning logic to reduce false alarms.
* Add a dashboard displaying drowsiness events.
* Evaluate the system on independent recording sessions.
* Explore additional driver-monitoring features.

## Disclaimer

This project is intended for educational and demonstration purposes only. It is not a certified vehicle safety system and must not be relied upon as a substitute for safe driving practices.
