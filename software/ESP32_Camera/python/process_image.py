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
edges = cv2.Canny(blur, 75, 150)

cv2.imwrite(str(OUTPUT_DIR / "original.jpg"), image)
cv2.imwrite(str(OUTPUT_DIR / "grayscale.jpg"), gray)
cv2.imwrite(str(OUTPUT_DIR / "blur.jpg"), blur)
cv2.imwrite(str(OUTPUT_DIR / "edges.jpg"), edges)

print("Saved processed images to data/processed/")
print("Finished.")
