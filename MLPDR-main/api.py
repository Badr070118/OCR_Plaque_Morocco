import os
from datetime import datetime

import arabic_reshaper
import cv2
from flask import Flask, jsonify, request, send_from_directory
from PIL import Image, UnidentifiedImageError

from detection import PlateDetector
from ocr import PlateReader


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(BASE_DIR, "tmp")
RECEIVED_DIR = os.path.join(BASE_DIR, "received")

os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(RECEIVED_DIR, exist_ok=True)

app = Flask(__name__)
_ENGINE = None


class LPDREngine:
    def __init__(self):
        self.detector = PlateDetector()
        self.detector.load_model(
            "./weights/detection/yolov3-detection_final.weights",
            "./weights/detection/yolov3-detection.cfg",
        )

        self.reader = PlateReader()
        self.reader.load_model(
            "./weights/ocr/yolov3-ocr_final.weights",
            "./weights/ocr/yolov3-ocr.cfg",
        )

    def _apply_trained_ocr(self):
        image, height, width, channels = self.reader.load_image("./tmp/plate_box.jpg")
        blob, outputs = self.reader.read_plate(image)
        boxes, confidences, class_ids = self.reader.get_boxes(outputs, width, height, threshold=0.3)
        segmented, plate_text = self.reader.draw_labels(boxes, confidences, class_ids, image)
        cv2.imwrite("./tmp/plate_segmented.jpg", segmented)
        return arabic_reshaper.reshape(plate_text)

    def _apply_tesseract_ocr(self):
        text = self.reader.tesseract_ocr("./tmp/plate_box.jpg")
        return text.strip()

    def process_image(self, image_path, ocr_mode="trained"):
        image, height, width, channels = self.detector.load_image(image_path)
        blob, outputs = self.detector.detect_plates(image)
        boxes, confidences, class_ids = self.detector.get_boxes(outputs, width, height, threshold=0.3)
        plate_img, lp_images = self.detector.draw_labels(boxes, confidences, class_ids, image)

        if not lp_images:
            return {
                "has_plate": False,
                "plate_text": "",
                "artifacts": {
                    "input": os.path.basename(image_path),
                    "detection": None,
                    "plate": None,
                    "segmented": None,
                },
            }

        cv2.imwrite("./tmp/car_box.jpg", plate_img)
        cv2.imwrite("./tmp/plate_box.jpg", lp_images[0])

        if ocr_mode == "tesseract":
            plate_text = self._apply_tesseract_ocr()
            segmented = None
        else:
            plate_text = self._apply_trained_ocr()
            segmented = "plate_segmented.jpg"

        return {
            "has_plate": True,
            "plate_text": plate_text,
            "artifacts": {
                "input": os.path.basename(image_path),
                "detection": "car_box.jpg",
                "plate": "plate_box.jpg",
                "segmented": segmented,
            },
        }


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = LPDREngine()
    return _ENGINE


@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "name": "Plate Detection-OCR API",
            "endpoints": {
                "upload": "POST /upload (multipart form-data: image, ocr_mode=trained|tesseract)",
                "artifact": "GET /artifacts/<filename>",
            },
        }
    )


@app.route("/upload", methods=["POST"])
def upload_image():
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image provided"}), 400

        uploaded_image = request.files["image"]
        if not uploaded_image or uploaded_image.filename == "":
            return jsonify({"error": "Invalid image file"}), 400

        ocr_mode = request.form.get("ocr_mode", "trained").strip().lower()
        if ocr_mode not in {"trained", "tesseract"}:
            return jsonify({"error": "Invalid ocr_mode. Use 'trained' or 'tesseract'."}), 400

        filename = "received_" + datetime.now().strftime("%Y_%m_%d-%H_%M_%S_%f") + ".jpg"
        image_path = os.path.join(RECEIVED_DIR, filename)

        try:
            image = Image.open(uploaded_image.stream).convert("RGB")
            image.save(image_path)
        except UnidentifiedImageError:
            return jsonify({"error": "Uploaded file is not a valid image"}), 400

        result = get_engine().process_image(image_path, ocr_mode=ocr_mode)

        ts = int(datetime.now().timestamp() * 1000)
        artifacts = {}
        for key, value in result["artifacts"].items():
            if not value:
                artifacts[key] = None
            elif key == "input":
                artifacts[key] = f"/received/{value}?t={ts}"
            else:
                artifacts[key] = f"/artifacts/{value}?t={ts}"

        return jsonify(
            {
                "result": result["plate_text"],
                "plate_text": result["plate_text"],
                "has_plate": result["has_plate"],
                "ocr_mode": ocr_mode,
                "artifacts": artifacts,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/artifacts/<path:filename>", methods=["GET"])
def artifact(filename):
    return send_from_directory(TMP_DIR, filename)


@app.route("/received/<path:filename>", methods=["GET"])
def received(filename):
    return send_from_directory(RECEIVED_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
