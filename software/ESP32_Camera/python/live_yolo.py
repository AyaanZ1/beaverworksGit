import time
import cv2
from ultralytics import YOLO

STREAM_URL = "http://192.168.1.4:81/stream"
MODEL_PATH = "yolo26n.pt"
CONFIDENCE_THRESHOLD = 0.35

print("Loading YOLO model...")
model = YOLO(MODEL_PATH)

print(f"Connecting to ESP32 stream: {STREAM_URL}")
capture = cv2.VideoCapture(STREAM_URL)

if not capture.isOpened():
    print("Could not connect to the ESP32 camera stream.")
    print("Confirm that the ESP32 is powered on and connected to the same Wi-Fi network.")
    raise SystemExit(1)

previous_time = time.perf_counter()
processed_frames = 0

print("Live YOLO started.")
print("Click the video window and press q to stop.")

try:
    while True:
        success, frame = capture.read()

        if not success:
            print("Failed to receive a frame from the ESP32.")
            break

        results = model.predict(
            source=frame,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False
        )

        result = results[0]
        annotated_frame = result.plot()

        current_time = time.perf_counter()
        elapsed = current_time - previous_time
        fps = 1.0 / elapsed if elapsed > 0 else 0.0
        previous_time = current_time

        boxes = result.boxes
        detection_count = 0 if boxes is None else len(boxes)

        cv2.putText(
            annotated_frame,
            f"FPS: {fps:.1f}",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        cv2.putText(
            annotated_frame,
            f"Objects: {detection_count}",
            (10, 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        cv2.imshow("ESP32 Live YOLO", annotated_frame)

        processed_frames += 1

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("Stopping live YOLO.")
            break

except KeyboardInterrupt:
    print("\nInterrupted from the terminal.")

finally:
    capture.release()
    cv2.destroyAllWindows()
    print(f"Frames processed: {processed_frames}")
    print("Finished.")
