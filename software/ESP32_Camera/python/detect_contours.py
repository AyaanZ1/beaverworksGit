from pathlib import Path
import cv2

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

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5, 5), 0)
edges = cv2.Canny(blur, 30, 100)

contours, _ = cv2.findContours(
    edges,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

result = image.copy()
kept_contours = 0

print(f"Contours found: {len(contours)}")

for index, contour in enumerate(contours, start=1):
    area = cv2.contourArea(contour)
    print(f"Contour {index} area: {area}")

    if area < 1:
        continue

    x, y, w, h = cv2.boundingRect(contour)
    cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
    kept_contours += 1

output_file = OUTPUT_DIR / "contours.jpg"
cv2.imwrite(str(output_file), result)

print(f"Contours kept: {kept_contours}")
print(f"Saved: {output_file}")
print("Finished.")
