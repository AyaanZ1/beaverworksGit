import time
import cv2

STREAM_URL = "http://192.168.1.4:81/stream"
TEST_SECONDS = 10

cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    print("Failed to connect to the camera stream.")
    raise SystemExit(1)

print(f"Measuring FPS for {TEST_SECONDS} seconds...")

start_time = time.time()
frame_count = 0

while time.time() - start_time < TEST_SECONDS:
    ret, frame = cap.read()

    if not ret:
        print("Failed to receive a frame.")
        break

    frame_count += 1

elapsed_time = time.time() - start_time
cap.release()

fps = frame_count / elapsed_time if elapsed_time > 0 else 0

print(f"Frames received: {frame_count}")
print(f"Elapsed time: {elapsed_time:.2f} seconds")
print(f"Average FPS: {fps:.2f}")
