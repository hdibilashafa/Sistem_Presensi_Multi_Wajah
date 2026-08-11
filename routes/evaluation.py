
import os
import json
import base64
import numpy as np
import cv2
from flask import Blueprint, request, jsonify, render_template
from database.models import ConfigModel, UserModel
from core.matcher import FaceMatcher
from core.detector import FaceDetector
from core.enhancer import ImageEnhancer
from core.extractor import FeatureExtractor
from core.embedding_cache import embedding_cache
from evaluation.roc_analysis import compute_roc, find_optimal_threshold, plot_roc_curve
from config import Config

evaluation_bp = Blueprint('evaluation', __name__)

                                                                       
                                                                        
                                                                        
                                
_detector = FaceDetector()
_enhancer = ImageEnhancer()
_extractor = FeatureExtractor()


def _decode_base64_image(base64_string):
    img_data = base64.b64decode(base64_string.split(',')[1])
    np_arr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return frame

                                                                  
EVAL_DATA_PATH = os.path.join(Config.BASE_DIR, 'evaluation', 'results', 'scores.json')


def _load_scores():
    if not os.path.exists(EVAL_DATA_PATH):
        return {'genuine': [], 'impostor': []}
    with open(EVAL_DATA_PATH, 'r') as f:
        return json.load(f)


def _save_scores(data):
    os.makedirs(os.path.dirname(EVAL_DATA_PATH), exist_ok=True)
    with open(EVAL_DATA_PATH, 'w') as f:
        json.dump(data, f)


@evaluation_bp.route('/admin/evaluation')
def evaluation_page():
    current_threshold = ConfigModel.get_threshold()
    scores = _load_scores()
    registered_users = [{'id': u['id'], 'nama': u['nama']} for u in UserModel.get_all()]
    return render_template(
        'admin/evaluation.html',
        current_threshold=current_threshold,
        genuine_scores=scores['genuine'],
        impostor_scores=scores['impostor'],
        total_genuine=len(scores['genuine']),
        total_impostor=len(scores['impostor']),
        registered_users=registered_users
    )


@evaluation_bp.route('/admin/evaluation/add_score', methods=['POST'])
def add_score():
    score = request.json.get('score')
    label = request.json.get('label')                             

    if score is None or label not in ('genuine', 'impostor'):
        return jsonify({'success': False, 'message': 'Data tidak valid.'}), 400

    data = _load_scores()
    data[label].append(float(score))
    _save_scores(data)

    return jsonify({
        'success': True,
        'genuine_scores': data['genuine'],
        'impostor_scores': data['impostor']
    })


@evaluation_bp.route('/admin/evaluation/delete_score', methods=['POST'])
def delete_score():
    label = request.json.get('label')
    index = request.json.get('index')

    if label not in ('genuine', 'impostor') or index is None:
        return jsonify({'success': False, 'message': 'Data tidak valid.'}), 400

    data = _load_scores()
    try:
        data[label].pop(int(index))
    except (IndexError, ValueError):
        return jsonify({'success': False, 'message': 'Data tidak ditemukan.'}), 400

    _save_scores(data)

    return jsonify({
        'success': True,
        'genuine_scores': data['genuine'],
        'impostor_scores': data['impostor']
    })


@evaluation_bp.route('/admin/evaluation/reset', methods=['POST'])
def reset_scores():
    _save_scores({'genuine': [], 'impostor': []})
    return jsonify({'success': True})


@evaluation_bp.route('/admin/evaluation/capture', methods=['POST'])
def capture_score():
    image_base64 = request.json.get('image')
    true_user_id = request.json.get('true_user_id') or None

    if not image_base64:
        return jsonify({'success': False, 'message': 'Frame kosong.'}), 400

    frame = _decode_base64_image(image_base64)
    if frame is None:
        return jsonify({'success': False, 'message': 'Gagal membaca frame.'}), 400

    faces = _detector.detect(frame)
    if not faces:
        return jsonify({'success': False, 'message': 'Tidak ada wajah terdeteksi pada frame ini.'}), 400

                                                                       
                                                                  
    face = max(faces, key=lambda f: f['confidence'])
    box = face['box']
    box_size = _detector.get_box_size(box)

    aligned_frame = _detector.align_face(frame, face['keypoints'])
    aligned_crop = _detector.crop_face(aligned_frame, box)
    if aligned_crop.size == 0:
        return jsonify({'success': False, 'message': 'Gagal memotong area wajah.'}), 400

    enhanced_rgb = _enhancer.process(aligned_crop, box_size)
    embedding = _extractor.extract(enhanced_rgb)

    reference_embeddings = embedding_cache.get_cached_embeddings()
    if not reference_embeddings:
        return jsonify({'success': False, 'message': 'Belum ada user dengan embedding di database.'}), 400

    data = _load_scores()
    breakdown = []

    for ref_user_id, ref_data in reference_embeddings.items():
        score = round(float(FaceMatcher.cosine_similarity(embedding, ref_data['embedding'])), 4)
        label = 'genuine' if (true_user_id is not None and ref_user_id == true_user_id) else 'impostor'

        data[label].append(score)
        breakdown.append({
            'user_id': ref_user_id,
            'nama': ref_data['nama'],
            'similarity': score,
            'label': label
        })

    _save_scores(data)

    return jsonify({
        'success': True,
        'breakdown': breakdown,
        'genuine_scores': data['genuine'],
        'impostor_scores': data['impostor']
    })


@evaluation_bp.route('/admin/evaluation/analyze', methods=['POST'])
def analyze_roc():
    data = _load_scores()
    genuine = np.array(data['genuine'])
    impostor = np.array(data['impostor'])

    if len(genuine) == 0 or len(impostor) == 0:
        return jsonify({
            'success': False,
            'message': 'Data genuine dan impostor harus tersedia sebelum analisis dapat dijalankan.'
        }), 400

    roc_table, auc_value = compute_roc(genuine, impostor)
    optimal = find_optimal_threshold(roc_table)
    plot_path = plot_roc_curve(roc_table, auc_value, optimal)

    return jsonify({
        'success': True,
        'roc_table': roc_table,
        'auc': round(auc_value, 4),
        'optimal_threshold': optimal['threshold'],
        'optimal_tpr': round(optimal['tpr'], 4),
        'optimal_fpr': round(optimal['fpr'], 4),
        'youden_index': round(optimal['youden_index'], 4),
        'plot_url': '/static/img/roc_curve.png'
    })


@evaluation_bp.route('/admin/evaluation/apply_threshold', methods=['POST'])
def apply_threshold():
    threshold = request.json.get('threshold')

    if threshold is None or not (0 <= float(threshold) <= 1):
        return jsonify({'success': False, 'message': 'Nilai threshold tidak valid.'}), 400

    ConfigModel.set_threshold(float(threshold))
    return jsonify({'success': True, 'message': f'Threshold berhasil diubah menjadi {threshold}.'})
