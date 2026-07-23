import cv2
import numpy as np

STREAM_URL = "http://192.168.1.4:81/stream"

capture = cv2.VideoCapture(STREAM_URL)

if not capture.isOpened():
    print("Could not open ESP32 camera stream.")
    raise SystemExit(1)

print("Starting live red-object detection.")
print("Press q in the video window to stop.")

while True:
    success, frame = capture.read()

    if not success:
        print("Failed to receive frame.")
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_red_1 = np.array([0, 100, 80])
    upper_red_1 = np.array([10, 255, 255])

    lower_red_2 = np.array([170, 100, 80])
    upper_red_2 = np.array([180, 255, 255])

    mask_1 = cv2.inRange(hsv, lower_red_1, upper_red_1)
    mask_2 = cv2.inRange(hsv, lower_red_2, upper_red_2)
    mask = cv2.bitwise_or(mask_1, mask_2)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    largest_contour = None
    largest_area = 0

    for contour in contours:
        area = cv2.contourArea(contour)

        if area > largest_area:
            largest_contour = contour
            largest_area = area

    if largest_contour is not None and largest_area > 300:
        x, y, w, h = cv2.boundingRect(largest_contour)
        center_x = x + w // 2
        center_y = y + h // 2

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        cv2.circle(
            frame,
            (center_x, center_y),
            5,
            (255, 0, 0),
            -1
        )

        cv2.putText(
            frame,
            f"Red object area: {int(largest_area)}",
            (x, max(20, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )

    cv2.imshow("Live Red Detection", frame)
    cv2.imshow("Red Mask", mask)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

capture.release()
cv2.destroyAllWindows()
print("Finished.")
