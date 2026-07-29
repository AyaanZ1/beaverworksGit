from ultralytics import YOLO
import cv2

# Load the YOLO detection model
model = YOLO("yolo11n.pt")

# Connect to the ESP32-CAM stream
stream = cv2.VideoCapture("http://192.168.1.4:81/stream")

while True:
    success, frame = stream.read()
    if not success:
        break

    # Detect objects and track consistent IDs
    results = model.track(
        frame,
        tracker="bytetrack.yaml",
        persist=True
    )

    # Draw detection boxes and tracking IDs
    annotated_frame = results[0].plot()

    # Display the processed camera feed
    cv2.imshow("Object Detection and Tracking", annotated_frame)

    # Press Q to stop
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

stream.release()
cv2.destroyAllWindows()


