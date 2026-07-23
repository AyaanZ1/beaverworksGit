from dataclasses import dataclass
from typing import Optional


@dataclass
class DetectedObject:
    class_name: str
    track_id: int
    center_x: int
    box_area: int
    confidence: float


@dataclass
class RobotCommand:
    action: str
    reason: str
    target_id: Optional[int] = None


def get_horizontal_position(center_x: int, frame_width: int) -> str:
    left_boundary = frame_width / 3
    right_boundary = 2 * frame_width / 3

    if center_x < left_boundary:
        return "LEFT"

    if center_x > right_boundary:
        return "RIGHT"

    return "CENTER"


def get_distance_category(box_area: int, frame_area: int) -> str:
    area_ratio = box_area / frame_area

    if area_ratio >= 0.35:
        return "VERY_CLOSE"

    if area_ratio >= 0.18:
        return "CLOSE"

    if area_ratio >= 0.07:
        return "MEDIUM"

    return "FAR"


def select_target(
    detections: list[DetectedObject],
    target_class: str = "person"
) -> Optional[DetectedObject]:
    matching_objects = [
        detection
        for detection in detections
        if detection.class_name == target_class
    ]

    if not matching_objects:
        return None

    return max(
        matching_objects,
        key=lambda detection: detection.box_area
    )


def choose_robot_command(
    target: Optional[DetectedObject],
    frame_width: int,
    frame_height: int
) -> RobotCommand:
    if target is None:
        return RobotCommand(
            action="SEARCH",
            reason="No target detected."
        )

    frame_area = frame_width * frame_height

    horizontal_position = get_horizontal_position(
        target.center_x,
        frame_width
    )

    distance = get_distance_category(
        target.box_area,
        frame_area
    )

    if distance == "VERY_CLOSE":
        return RobotCommand(
            action="STOP",
            reason="Target is very close.",
            target_id=target.track_id
        )

    if horizontal_position == "LEFT":
        return RobotCommand(
            action="TURN_LEFT",
            reason=f"Target is left and {distance.lower()}.",
            target_id=target.track_id
        )

    if horizontal_position == "RIGHT":
        return RobotCommand(
            action="TURN_RIGHT",
            reason=f"Target is right and {distance.lower()}.",
            target_id=target.track_id
        )

    if distance in {"FAR", "MEDIUM"}:
        return RobotCommand(
            action="FORWARD",
            reason=f"Target is centered and {distance.lower()}.",
            target_id=target.track_id
        )

    return RobotCommand(
        action="STOP",
        reason="Target is centered and close.",
        target_id=target.track_id
    )


def main() -> None:
    frame_width = 640
    frame_height = 480

    sample_detections = [
        DetectedObject(
            class_name="person",
            track_id=3,
            center_x=175,
            box_area=28000,
            confidence=0.88
        ),
        DetectedObject(
            class_name="chair",
            track_id=7,
            center_x=500,
            box_area=18000,
            confidence=0.76
        )
    ]

    target = select_target(
        sample_detections,
        target_class="person"
    )

    command = choose_robot_command(
        target,
        frame_width,
        frame_height
    )

    print(f"Command: {command.action}")
    print(f"Reason: {command.reason}")
    print(f"Target ID: {command.target_id}")


if __name__ == "__main__":
    main()
