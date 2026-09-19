"""Optional MediaPipe live/image vision adapter for Chimera.
Model files are deployment assets and are never downloaded implicitly."""
from __future__ import annotations

def detect(image, task="face"):
    import mediapipe as mp
    if task == "face":
        detector = mp.tasks.vision.FaceDetector.create_from_options(mp.tasks.vision.FaceDetectorOptions(base_options=mp.tasks.BaseOptions(model_asset_path="face_detector.task")))
        return detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=image))
    raise ValueError("unsupported task; configure a local MediaPipe model for face/object/pose/gesture/segmentation")
