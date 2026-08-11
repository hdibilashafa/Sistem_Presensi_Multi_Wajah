
import cv2
import numpy as np
import base64
from flask import Blueprint, request, jsonify, render_template
from config import Config
from database.models import PresensiModel
from core.detector import FaceDetector
from core.enhancer import ImageEnhancer
from core.extractor import FeatureExtractor
from core.matcher import FaceMatcher
from core.embedding_cache import embedding_cache
from database.models import ConfigModel

presence_bp = Blueprint('presence', __name__)

                                                                       
detector = FaceDetector()
enhancer = ImageEnhancer()
extractor = FeatureExtractor()
matcher = FaceMatcher(threshold=Config.DEFAULT_THRESHOLD)

                                                                         
                                                                       
                                                           
session_embeddings = {}

                                                               
                                                                                
session_recorded_users = set()


def _decode_base64_image(base64_string):
    img_data = base64.b64decode(base64_string.split(',')[1])
    np_arr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return frame


@presence_bp.route('/presence')
def presence_page():
    return render_template('admin/presence.html')


@presence_bp.route('/presence/start', methods=['POST'])
def start_presence_session():
    global session_embeddings, session_recorded_users

    session_embeddings = embedding_cache.get_cached_embeddings()
    session_recorded_users = set()

    threshold = ConfigModel.get_threshold()
    matcher.set_threshold(threshold)

    return jsonify({
        'success': True,
        'total_user_terdaftar': len(session_embeddings),
        'threshold': threshold
    })


@presence_bp.route('/presence/frame', methods=['POST'])
def process_frame():
    image_base64 = request.json.get('image')
    if not image_base64:
        return jsonify({'success': False, 'message': 'Frame kosong.'}), 400

    frame = _decode_base64_image(image_base64)
    if frame is None:
        return jsonify({'success': False, 'message': 'Gagal membaca frame.'}), 400

                                                       
    faces = detector.detect(frame)

    results = []
    for face in faces:
        box = face['box']
        x, y, w, h = box
        box_size = detector.get_box_size(box)

                           
        aligned_frame = detector.align_face(frame, face['keypoints'])
        aligned_crop = detector.crop_face(aligned_frame, box)

        if aligned_crop.size == 0:
            continue

                                                           
        enhanced_rgb = enhancer.process(aligned_crop, box_size)

                            
        embedding = extractor.extract(enhanced_rgb)

                                                                                     
                                                  
        match_result = matcher.match(embedding, session_embeddings)

                                                
                                   
                                                                                     
                                                                                    
                                                              
        already_recorded_today = False
        if match_result['recognized']:
            user_id = match_result['user_id']

            if user_id in session_recorded_users:
                already_recorded_today = True
            elif PresensiModel.already_presensi_today(user_id):
                already_recorded_today = True
                session_recorded_users.add(user_id)                         
            else:
                PresensiModel.save(user_id, match_result['similarity'])
                session_recorded_users.add(user_id)

        results.append({
            'box': {'x': x, 'y': y, 'w': w, 'h': h},
            'recognized': match_result['recognized'],
            'nama': match_result['nama'],
            'similarity': round(match_result['similarity'], 4),
            'already_recorded_today': already_recorded_today
        })

    return jsonify({
        'success': True,
        'total_wajah': len(results),
        'faces': results
    })


@presence_bp.route('/presence/stop', methods=['POST'])
def stop_presence_session():
    global session_recorded_users
    total_recorded = len(session_recorded_users)
    session_recorded_users = set()

    return jsonify({
        'success': True,
        'total_tercatat': total_recorded
    })
