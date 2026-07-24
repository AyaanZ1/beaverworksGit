import time
from collections import deque
from pathlib import Path

import cv2
import streamlit as st
import pandas as pd
from ultralytics import YOLO


STREAM_URL = "http://192.168.1.4:81/stream"
MODEL_PATH = Path("yolo26n.pt")

TARGET_CLASS = "person"
CONFIRMATION_FRAMES = 3
TARGET_LOSS_DELAY = 0.75


st.set_page_config(
    page_title="Robot Vision Dashboard",
    page_icon="🤖",
    layout="wide",
)

if "detection_log" not in st.session_state:
    st.session_state.detection_log = []

st.title("🤖 Robot Vision Dashboard")
st.caption("ESP32-CAM object detection, tracking, and navigation monitor")


@st.cache_resource
def load_model(model_path: str) -> YOLO:
    return YOLO(model_path)


def choose_command(
    center_x: float,
    frame_width: int,
    box_width: float,
) -> str:
    left_boundary = frame_width * 0.40
    right_boundary = frame_width * 0.60
    width_ratio = box_width / frame_width

    if width_ratio > 0.55:
        return "STOP"

    if center_x < left_boundary:
        return "TURN_LEFT"

    if center_x > right_boundary:
        return "TURN_RIGHT"

    return "FORWARD"


if not MODEL_PATH.exists():
    st.error(f"Model not found: {MODEL_PATH}")
    st.stop()

model = load_model(str(MODEL_PATH))

st.sidebar.header("Controls")

confidence_threshold = st.sidebar.slider(
    "Detection confidence",
    min_value=0.10,
    max_value=1.00,
    value=0.20,
    step=0.05,
)

target_class = st.sidebar.text_input(
    "Target object",
    value=TARGET_CLASS,
).strip().lower()

start_camera = st.sidebar.toggle(
    "Start ESP32-CAM",
    value=False,
)

st.sidebar.code(STREAM_URL)

video_column, status_column = st.columns([3, 1])

with video_column:
    st.subheader("Live ESP32-CAM Feed")
    video_placeholder = st.empty()

with status_column:
    st.subheader("System Status")
    camera_status = st.empty()
    detection_status = st.empty()
    command_status = st.empty()
    fps_status = st.empty()

    st.subheader("Target Information")
    target_status = st.empty()
    track_status = st.empty()
    confidence_status = st.empty()
    position_status = st.empty()

st.subheader("Recent Detection History")
history_placeholder = st.empty()


if not start_camera:
    camera_status.info("Camera: Off")
    detection_status.info("Detection: Waiting")
    command_status.info("Command: STOP")
    fps_status.metric("FPS", "0.0")
    target_status.write("Target: None")
    track_status.write("Tracking ID: --")
    confidence_status.write("Confidence: --")
    position_status.write("Position: --")
    st.stop()


capture = cv2.VideoCapture(STREAM_URL)

if not capture.isOpened():
    camera_status.error("Camera: Connection failed")
    st.error(f"Could not open {STREAM_URL}")
    st.stop()

camera_status.success("Camera: Connected")

previous_time = time.perf_counter()
last_target_time = 0.0
displayed_command = "SEARCH"
command_history = deque(maxlen=CONFIRMATION_FRAMES)

try:
    while start_camera:
        success, frame = capture.read()

        if not success or frame is None:
            camera_status.error("Camera: Frame read failed")
            break

        frame_height, frame_width = frame.shape[:2]

        results = model.track(
            source=frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=confidence_threshold,
            verbose=False,
        )

        result = results[0]
        annotated_frame = result.plot()

        best_target = None

        if result.boxes is not None and len(result.boxes) > 0:
            classes = result.boxes.cls.int().cpu().tolist()
            confidences = result.boxes.conf.cpu().tolist()
            boxes = result.boxes.xyxy.cpu().tolist()

            if result.boxes.id is not None:
                track_ids = result.boxes.id.int().cpu().tolist()
            else:
                track_ids = [-1] * len(boxes)

            for track_id, class_id, confidence, box in zip(
                track_ids,
                classes,
                confidences,
                boxes,
            ):
                class_name = model.names[class_id].lower()

                if class_name != target_class:
                    continue

                x1, y1, x2, y2 = box

                candidate = {
                    "class_name": class_name,
                    "confidence": confidence,
                    "track_id": track_id,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                }

                if (
                    best_target is None
                    or confidence > best_target["confidence"]
                ):
                    best_target = candidate

        current_time = time.perf_counter()

        if best_target is not None:
            x1 = best_target["x1"]
            y1 = best_target["y1"]
            x2 = best_target["x2"]
            y2 = best_target["y2"]

            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            box_width = x2 - x1

            raw_command = choose_command(
                center_x=center_x,
                frame_width=frame_width,
                box_width=box_width,
            )

            last_target_time = current_time
            command_history.append(raw_command)

            if (
                len(command_history) == CONFIRMATION_FRAMES
                and len(set(command_history)) == 1
            ):
                displayed_command = raw_command

            cv2.circle(
                annotated_frame,
                (int(center_x), int(center_y)),
                6,
                (255, 255, 255),
                -1,
            )

            cv2.line(
                annotated_frame,
                (int(frame_width * 0.40), 0),
                (int(frame_width * 0.40), frame_height),
                (255, 255, 255),
                1,
            )

            cv2.line(
                annotated_frame,
                (int(frame_width * 0.60), 0),
                (int(frame_width * 0.60), frame_height),
                (255, 255, 255),
                1,
            )

            detection_status.success("Detection: Target found")
            target_status.write(
                f"Target: {best_target['class_name']}"
            )
            track_status.write(
                f"Tracking ID: {best_target['track_id']}"
            )
            confidence_status.write(
                f"Confidence: {best_target['confidence']:.1%}"
            )
            position_status.write(
                f"Center: ({int(center_x)}, {int(center_y)})"
            )

            log_entry = {
                "Time": time.strftime("%H:%M:%S"),
                "Object": best_target["class_name"],
                "Tracking ID": best_target["track_id"],
                "Confidence": round(
                    best_target["confidence"] * 100,
                    1,
                ),
                "Command": displayed_command,
            }

            if (
                not st.session_state.detection_log
                or st.session_state.detection_log[-1]["Command"]
                != displayed_command
                or st.session_state.detection_log[-1]["Tracking ID"]
                != best_target["track_id"]
            ):
                st.session_state.detection_log.append(log_entry)
                st.session_state.detection_log = (
                    st.session_state.detection_log[-15:]
                )

        else:
            if current_time - last_target_time >= TARGET_LOSS_DELAY:
                displayed_command = "SEARCH"
                command_history.clear()

            detection_status.warning("Detection: Target not found")
            target_status.write(f"Target: {target_class}")
            track_status.write("Tracking ID: --")
            confidence_status.write("Confidence: --")
            position_status.write("Center: --")

        if displayed_command == "STOP":
            command_status.error("Command: STOP")
        elif displayed_command == "SEARCH":
            command_status.warning("Command: SEARCH")
        else:
            command_status.success(
                f"Command: {displayed_command}"
            )

        elapsed = current_time - previous_time
        previous_time = current_time
        fps = 1.0 / elapsed if elapsed > 0 else 0.0

        annotated_rgb = cv2.cvtColor(
            annotated_frame,
            cv2.COLOR_BGR2RGB,
        )

        video_placeholder.image(
            annotated_rgb,
            channels="RGB",
            use_container_width=True,
        )

        fps_status.metric("FPS", f"{fps:.1f}")

        if st.session_state.detection_log:
            history_dataframe = pd.DataFrame(
                reversed(st.session_state.detection_log)
            )

            history_placeholder.dataframe(
                history_dataframe,
                use_container_width=True,
                hide_index=True,
            )
        else:
            history_placeholder.info(
                "No target detections recorded yet."
            )

finally:
    capture.release()
