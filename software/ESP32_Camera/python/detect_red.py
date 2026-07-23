from pathlib import Path
import cv2
import numpy as np

IMAGE_DIR = Path("data/images")
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

images = sorted(IMAGE_DIR.glob("*.jpg"))

if not images:
    print("No images found.")
    raise SystemExit(1)

image_file = images[-1]
print(f"Loading: {image_file}")

image = cv2.imread(str(image_file))

if image is None:
    print("Failed to load image.")
    raise SystemExit(1)

hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

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

result = image.copy()
detected = 0

for contour in contours:
    area = cv2.contourArea(contour)

    if area < 100:
        continue

    x, y, w, h = cv2.boundingRect(contour)

    cv2.rectangle(
        result,
        (x, y),
        (x + w, y + h),
        (0, 255, 0),
        2
    )

    cv2.putText(
        result,
        f"Red object: {int(area)} px",
        (x, max(20, y - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        2
    )

    detected += 1

mask_file = OUTPUT_DIR / "red_mask.jpg"
result_file = OUTPUT_DIR / "red_detection.jpg"

cv2.imwrite(str(mask_file), mask)
cv2.imwrite(str(result_file), result)

print(f"Red objects detected: {detected}")
print(f"Saved mask: {mask_file}")
print(f"Saved detection: {result_file}")
print("Finished.")
