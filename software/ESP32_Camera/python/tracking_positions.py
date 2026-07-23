import time
import cv2
from ultralytics import YOLO

STREAM_URL = "http://192.168.1.4:81/stream"
MODEL_PATH = "yolo26n.pt"
CONFIDENCE_THRESHOLD = 0.35


def get_horizontal_position(center_x: int, frame_width: int) -> str:
    left_boundary = frame_width / 3
    right_boundary = 2 * frame_width / 3

    if center_x < left_boundary:
        return "LEFT"

    if center_x > right_boundary:
        return "RIGHT"

    return "CENTER"


print("Loading YOLO model...")
model = YOLO(MODEL_PATH)

print(f"Connecting to ESP32 stream: {STREAM_URL}")
capture = cv2.VideoCapture(STREAM_URL)

if not capture.isOpened():
    print("Could not connect to the ESP32 camera stream.")
    raise SystemExit(1)

previous_time = time.perf_counter()

print("Object-position tracking started.")
print("Press q in the video window to stop.")

try:
    while True:
        success, frame = capture.read()

        if not success:
            print("Failed to receive a frame.")
            break

        frame_height, frame_width = frame.shape[:2]

        results = model.track(
            source=frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=CONFIDENCE_THRESHOLD,
            verbose=False
        )

        result = results[0]
        annotated_frame = result.plot()

        current_time = time.perf_counter()
        elapsed = current_time - previous_time
        fps = 1.0 / elapsed if elapsed > 0 else 0.0
        previous_time = current_time

        if (
            result.boxes is not None
            and result.boxes.id is not None
            and result.boxes.xyxy is not None
        ):
            track_ids = result.boxes.id.int().cpu().tolist()
            class_ids = result.boxes.cls.int().cpu().tolist()
            boxes = result.boxes.xyxy.cpu().tolist()

            for track_id, class_id, box in zip(track_ids, class_ids, boxes):
                x1, y1, x2, y2 = map(int, box)

                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                box_width = x2 - x1
                box_height = y2 - y1
                box_area = box_width * box_height

                horizontal_position = get_horizontal_position(
                    center_x,
                    frame_width
                )

                class_name = model.names[class_id]

                label = (
                    f"{class_name} ID:{track_id} "
                    f"{horizontal_position}"
                )

                cv2.circle(
                    annotated_frame,
                    (center_x, center_y),
                    5,
                    (0, 0, 255),
                    -1
                )

                cv2.putText(
                    annotated_frame,
                    label,
                    (x1, max(y1 - 25, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    2
                )

                print(
                    f"Object={class_name}, "
                    f"ID={track_id}, "
                    f"Center=({center_x}, {center_y}), "
                    f"Position={horizontal_position}, "
                    f"Box area={box_area}"
                )

        cv2.putText(
            annotated_frame,
            f"FPS: {fps:.1f}",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        cv2.line(
            annotated_frame,
            (frame_width // 3, 0),
            (frame_width // 3, frame_height),
            (255, 255, 255),
            1
        )

        cv2.line(
            annotated_frame,
            (2 * frame_width // 3, 0),
            (2 * frame_width // 3, frame_height),
            (255, 255, 255),
            1
        )

        cv2.imshow("ESP32 Object Positions", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:
    print("\nInterrupted from the terminal.")

finally:
    capture.release()
    cv2.destroyAllWindows()
    print("Finished.")
