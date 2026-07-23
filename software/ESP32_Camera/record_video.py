from datetime import datetime
from pathlib import Path
import time

import cv2

STREAM_URL = "http://192.168.1.4:81/stream"
VIDEO_DIR = Path("data/videos")
RECORD_SECONDS = 10

VIDEO_DIR.mkdir(parents=True, exist_ok=True)

cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    print("Failed to connect to the camera stream.")
    raise SystemExit(1)

ret, frame = cap.read()

if not ret:
    print("Failed to receive the first frame.")
    cap.release()
    raise SystemExit(1)

height, width = frame.shape[:2]
fps = 10.0

filename = VIDEO_DIR / f"camera_{datetime.now():%Y%m%d_%H%M%S}.mp4"

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(
    str(filename),
    fourcc,
    fps,
    (width, height),
)

if not writer.isOpened():
    print("Failed to create the video file.")
    cap.release()
    raise SystemExit(1)

print(f"Recording for {RECORD_SECONDS} seconds...")

start_time = time.time()
frames_written = 0

while time.time() - start_time < RECORD_SECONDS:
    ret, frame = cap.read()

    if not ret:
        print("Failed to receive a frame.")
        break

    writer.write(frame)
    frames_written += 1

writer.release()
cap.release()

print(f"Saved video: {filename}")
print(f"Frames recorded: {frames_written}")