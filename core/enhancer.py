
import cv2
import numpy as np
from config import Config


class ImageEnhancer:
    def __init__(self):
        self.target_size = Config.INPUT_SIZE              
        self.clahe = cv2.createCLAHE(
            clipLimit=Config.CLAHE_CLIP_LIMIT,
            tileGridSize=Config.CLAHE_TILE_GRID_SIZE
        )

    def process(self, face_crop_bgr, box_size):
        if box_size < Config.ENHANCEMENT_THRESHOLD:
                                                       
            resized = self._bicubic_resize(face_crop_bgr)
            enhanced = self._apply_clahe(resized)
            sharpened = self._unsharp_masking(enhanced)
            result_bgr = sharpened
        else:
                                                                                 
            result_bgr = self._bicubic_resize(face_crop_bgr)

                                                                         
        result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
        return result_rgb

    def _bicubic_resize(self, image_bgr):
        return cv2.resize(image_bgr, self.target_size, interpolation=cv2.INTER_CUBIC)

    def _apply_clahe(self, image_bgr):
        lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        l_clahe = self.clahe.apply(l_channel)

        lab_clahe = cv2.merge((l_clahe, a_channel, b_channel))
        result_bgr = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
        return result_bgr

    def _unsharp_masking(self, image_bgr):
        blurred = cv2.GaussianBlur(image_bgr, (0, 0), sigmaX=Config.UNSHARP_SIGMA)
        sharpened = cv2.addWeighted(
            image_bgr, 1.0 + Config.UNSHARP_STRENGTH,
            blurred, -Config.UNSHARP_STRENGTH,
            0
        )
        return sharpened
