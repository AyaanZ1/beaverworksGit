import time
from collections import deque

import cv2
from ultralytics import YOLO

from robot_decision_logic import (
    DetectedObject,
    select_target,
    choose_robot_command,
)

STREAM_URL = "http://192.168.1.4:81/stream"
MODEL_PATH = "yolo26n.pt"

CONFIDENCE_THRESHOLD = 0.20
TARGET_CLASS = "person"
COMMAND_CONFIRMATION_FRAMES = 3
TARGET_LOSS_DELAY = 0.75

model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    raise RuntimeError("Could not connect to ESP32 camera.")

previous_time = time.perf_counter()

command_history = deque(maxlen=COMMAND_CONFIRMATION_FRAMES)
displayed_command = "SEARCH"
last_target_time = 0.0

while True:
    success, frame = cap.read()

    if not success:
        print("Camera frame could not be read.")
        break

    height, width = frame.shape[:2]

    results = model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        conf=CONFIDENCE_THRESHOLD,
        verbose=False,
    )

    result = results[0]
    annotated = result.plot()
    detections = []

    # Accept YOLO detections even before ByteTrack assigns IDs.
    if result.boxes is not None and len(result.boxes) > 0:
        classes = result.boxes.cls.int().cpu().tolist()
        confs = result.boxes.conf.cpu().tolist()
        boxes = result.boxes.xyxy.cpu().tolist()

        if result.boxes.id is not None:
            track_ids = result.boxes.id.int().cpu().tolist()
        else:
            track_ids = [-1] * len(boxes)

        for track_id, class_id, confidence, box in zip(
            track_ids,
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
                    confidence=confidence,
                )
            )

    target = select_target(
        detections,
        target_class=TARGET_CLASS,
    )

    raw_command = choose_robot_command(
        target,
        width,
        height,
    ).action

    current_time = time.perf_counter()

    if target is not None:
        last_target_time = current_time
        command_history.append(raw_command)

        if (
            len(command_history) == COMMAND_CONFIRMATION_FRAMES
            and len(set(command_history)) == 1
        ):
            displayed_command = raw_command

    elif current_time - last_target_time >= TARGET_LOSS_DELAY:
        displayed_command = "SEARCH"
        command_history.clear()

    elapsed = current_time - previous_time
    fps = 1.0 / elapsed if elapsed > 0 else 0.0
    previous_time = current_time

    person_count = sum(
        detection.class_name.lower() == TARGET_CLASS
        for detection in detections
    )

    target_text = (
        f"Target: detected | ID: {target.track_id}"
        if target is not None
        else "Target: not detected"
    )

    cv2.putText(
        annotated,
        f"Command: {displayed_command}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
    )

    cv2.putText(
        annotated,
        target_text,
        (10, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 0),
        2,
    )

    cv2.putText(
        annotated,
        f"People: {person_count} | FPS: {fps:.1f}",
        (10, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 0),
        2,
    )

    cv2.imshow("Robot Brain", annotated)

    print(
        f"raw={raw_command:<10} "
        f"output={displayed_command:<10} "
        f"people={person_count}"
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
