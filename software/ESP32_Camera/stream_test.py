from datetime import datetime
from pathlib import Path

import cv2

STREAM_URL = "http://192.168.1.4:81/stream"
IMAGE_DIR = Path("data/images")

IMAGE_DIR.mkdir(parents=True, exist_ok=True)

cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    print("Failed to connect to the camera stream.")
    raise SystemExit(1)

ret, frame = cap.read()

if not ret:
    print("Failed to receive a frame.")
    cap.release()
    raise SystemExit(1)

filename = IMAGE_DIR / f"camera_{datetime.now():%Y%m%d_%H%M%S}.jpg"

if cv2.imwrite(str(filename), frame):
    print(f"Saved image: {filename}")
else:
    print("Failed to save the image.")

cap.release()