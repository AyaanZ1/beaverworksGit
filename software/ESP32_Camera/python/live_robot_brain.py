import time
import cv2
from ultralytics import YOLO

from robot_decision_logic import (
    DetectedObject,
    select_target,
    choose_robot_command,
)

STREAM_URL = "http://192.168.1.4:81/stream"
MODEL_PATH = "yolo26n.pt"

model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    raise RuntimeError("Could not connect to ESP32 camera.")

previous_time = time.perf_counter()

while True:

    success, frame = cap.read()

    if not success:
        break

    height, width = frame.shape[:2]

    results = model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        conf=0.35,
        verbose=False,
    )

    result = results[0]

    annotated = result.plot()

    detections = []

    if (
        result.boxes is not None
        and result.boxes.id is not None
    ):

        ids = result.boxes.id.int().cpu().tolist()
        classes = result.boxes.cls.int().cpu().tolist()
        confs = result.boxes.conf.cpu().tolist()
        boxes = result.boxes.xyxy.cpu().tolist()

        for track_id, class_id, conf, box in zip(
            ids,
            classes,
            confs,
            boxes,
        ):

            x1, y1, x2, y2 = map(int, box)

            detections.append(
                DetectedObject(
                    class_name=model.names[class_id],
                    track_id=track_id,
                    center_x=(x1 + x2) // 2,
                    box_area=(x2 - x1) * (y2 - y1),
                    confidence=conf,
                )
            )

    target = select_target(
        detections,
        target_class="person",
    )

    command = choose_robot_command(
        target,
        width,
        height,
    )

    current = time.perf_counter()
    fps = 1.0 / (current - previous_time)
    previous_time = current

    cv2.putText(
        annotated,
        f"Command: {command.action}",
        (10,30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0,255,0),
        2,
    )

    cv2.putText(
        annotated,
        f"FPS: {fps:.1f}",
        (10,65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0,255,0),
        2,
    )

    cv2.imshow("Robot Brain", annotated)

    print(command.action)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
