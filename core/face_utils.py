import base64
import binascii
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np


FACE_MODELS_DIR = Path(__file__).resolve().parent / "face_models"
DETECTOR_MODEL = FACE_MODELS_DIR / "face_detection_yunet_2023mar.onnx"
RECOGNIZER_MODEL = FACE_MODELS_DIR / "face_recognition_sface_2021dec.onnx"


@lru_cache(maxsize=1)
def _get_detector():
    if not DETECTOR_MODEL.is_file():
        raise RuntimeError(f"Face detector model not found: {DETECTOR_MODEL}")

    return cv2.FaceDetectorYN_create(
        str(DETECTOR_MODEL), "", (320, 320), 0.9, 0.3, 5000
    )


@lru_cache(maxsize=1)
def _get_recognizer():
    if not RECOGNIZER_MODEL.is_file():
        raise RuntimeError(f"Face recognition model not found: {RECOGNIZER_MODEL}")

    return cv2.FaceRecognizerSF_create(str(RECOGNIZER_MODEL), "")


def face_template_from_data_url(image_data):
    """Create a numeric face template from a browser camera data URL."""
    if not image_data or "," not in image_data:
        raise ValueError("No captured image was received.")

    try:
        image_bytes = base64.b64decode(image_data.split(",", 1)[1], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("The captured image data is invalid.") from exc

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("The captured image could not be read.")

    height, width = image.shape[:2]
    detector = _get_detector()
    detector.setInputSize((width, height))
    _, faces = detector.detect(image)

    if faces is None or len(faces) == 0:
        raise ValueError("No face was detected. Improve the lighting and try again.")

    if len(faces) != 1:
        raise ValueError("Only one face should be visible during registration.")

    recognizer = _get_recognizer()
    aligned_face = recognizer.alignCrop(image, faces[0])
    feature = recognizer.feature(aligned_face).flatten().astype(np.float32)

    norm = np.linalg.norm(feature)
    if norm == 0:
        raise ValueError("Could not create a face template. Please try again.")

    feature /= norm
    return feature.tolist()


def face_similarity(first_template, second_template):
    """Return cosine similarity for two saved face templates."""
    first = np.asarray(first_template, dtype=np.float32).flatten()
    second = np.asarray(second_template, dtype=np.float32).flatten()

    if first.size == 0 or second.size == 0 or first.size != second.size:
        return 0.0

    first_norm = np.linalg.norm(first)
    second_norm = np.linalg.norm(second)

    if first_norm == 0 or second_norm == 0:
        return 0.0

    return float(np.dot(first, second) / (first_norm * second_norm))