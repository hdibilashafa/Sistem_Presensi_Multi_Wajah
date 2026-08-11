
import cv2
import numpy as np
from mtcnn import MTCNN
from config import Config


class FaceDetector:
    def __init__(self):
        self.detector = MTCNN(
            min_face_size=Config.MIN_FACE_SIZE,
            scale_factor=Config.MTCNN_SCALE_FACTOR,
        )

    def detect(self, frame_bgr):
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self.detector.detect_faces(frame_rgb)

        faces = []
        for res in results:
            x, y, w, h = res['box']
            x, y = max(0, x), max(0, y)
            faces.append({
                'box': (x, y, w, h),
                'confidence': res['confidence'],
                'keypoints': res['keypoints']
            })
        return faces

    def crop_face(self, frame_bgr, box):
        x, y, w, h = box
        frame_h, frame_w = frame_bgr.shape[:2]

        x2 = min(x + w, frame_w)
        y2 = min(y + h, frame_h)
        x = max(0, x)
        y = max(0, y)

        face_crop = frame_bgr[y:y2, x:x2]
        return face_crop

    def align_face(self, frame_bgr, keypoints, output_size=None):
        if output_size is None:
            output_size = Config.INPUT_SIZE

        left_eye = np.array(keypoints['left_eye'], dtype=np.float64)
        right_eye = np.array(keypoints['right_eye'], dtype=np.float64)

        dy = right_eye[1] - left_eye[1]
        dx = right_eye[0] - left_eye[0]
        angle = np.degrees(np.arctan2(dy, dx))

        eyes_center = (
            float((left_eye[0] + right_eye[0]) / 2),
            float((left_eye[1] + right_eye[1]) / 2)
        )

        rot_matrix = cv2.getRotationMatrix2D(eyes_center, angle, 1.0)
        aligned = cv2.warpAffine(
            frame_bgr, rot_matrix,
            (frame_bgr.shape[1], frame_bgr.shape[0]),
            flags=cv2.INTER_CUBIC
        )
        return aligned

    def get_box_size(self, box):
        _, _, w, h = box
        return min(w, h)
