from pathlib import Path
from ultralytics import YOLO
import cv2

IMAGE_DIR = Path("data/images")
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

images = sorted(IMAGE_DIR.glob("*.jpg"))

if not images:
    print("No camera images found.")
    raise SystemExit(1)

image_file = images[-1]
print(f"Loading: {image_file}")

# Small pretrained model suitable for an initial test.
model = YOLO("yolo26n.pt")

results = model.predict(
    source=str(image_file),
    conf=0.25,
    verbose=False
)

annotated = results[0].plot()
output_file = OUTPUT_DIR / "object_detection.jpg"

cv2.imwrite(str(output_file), annotated)

boxes = results[0].boxes
count = 0 if boxes is None else len(boxes)

print(f"Objects detected: {count}")

if boxes is not None:
    for box in boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = model.names[class_id]
        print(f"- {class_name}: {confidence:.2f}")

print(f"Saved: {output_file}")
print("Finished.")
