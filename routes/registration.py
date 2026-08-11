
import os
import shutil
import cv2
import numpy as np
from flask import Blueprint, request, jsonify, render_template
from config import Config
from database.models import UserModel, EmbeddingModel
from core.detector import FaceDetector
from core.enhancer import ImageEnhancer
from core.extractor import FeatureExtractor
from core.embedding_cache import embedding_cache

registration_bp = Blueprint('registration', __name__)

                                                                              
                                                                               
detector = FaceDetector()
enhancer = ImageEnhancer()
extractor = FeatureExtractor()


def _get_user_dataset_paths(user_id):
    base = os.path.join(Config.DATASET_FOLDER, str(user_id))
    paths = {
        'input': os.path.join(base, 'input'),
        'mtcnn_output': os.path.join(base, 'mtcnn_output'),
        'aligned': os.path.join(base, 'aligned'),
        'enhanced': os.path.join(base, 'enhanced'),
    }
    for p in paths.values():
        os.makedirs(p, exist_ok=True)
    return paths


@registration_bp.route('/registration')
def registration_page():
    return render_template(
        'admin/registration.html',
        distances=Config.REGISTRATION_DISTANCES,
        expressions=Config.REGISTRATION_EXPRESSIONS,
        total_photos=Config.PHOTOS_PER_USER
    )


@registration_bp.route('/registration/start', methods=['POST'])
def start_registration():
    user_id = request.form.get('user_id', '').strip()
    nama = request.form.get('nama', '').strip()

    if not nama:
        return jsonify({'success': False, 'message': 'Nama tidak boleh kosong.'}), 400

    if not user_id.isdigit() or len(user_id) != 8:
        return jsonify({
            'success': False,
            'message': 'ID harus berupa 8 digit angka, contoh: 20240001.'
        }), 400

                                                                       
                                                                           
                                                                  
    if UserModel.exists(user_id):
        return jsonify({
            'success': False,
            'message': f'ID {user_id} sudah terdaftar. Gunakan ID lain.'
        }), 400

    user_folder = os.path.join(Config.DATASET_FOLDER, str(user_id))
    if os.path.exists(user_folder):
        return jsonify({
            'success': False,
            'message': f'ID {user_id} sedang dipakai pada sesi registrasi lain yang belum selesai. Gunakan ID lain atau hubungi admin.'
        }), 400

                                                                    
                                                                        
                                                                    
    paths = _get_user_dataset_paths(user_id)
    with open(os.path.join(os.path.dirname(paths['input']), '_nama.txt'), 'w', encoding='utf-8') as f:
        f.write(nama)

    return jsonify({
        'success': True,
        'user_id': user_id,
        'nama': nama,
        'distances': Config.REGISTRATION_DISTANCES,
        'expressions': Config.REGISTRATION_EXPRESSIONS
    })


@registration_bp.route('/registration/cancel', methods=['POST'])
def cancel_registration():
    user_id = request.form.get('user_id', '').strip()
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id tidak ditemukan.'}), 400

    if UserModel.exists(user_id):
        UserModel.delete(user_id)

    user_folder = os.path.join(Config.DATASET_FOLDER, str(user_id))
    if os.path.exists(user_folder):
        shutil.rmtree(user_folder)

    return jsonify({'success': True, 'message': 'Registrasi dibatalkan.'})


@registration_bp.route('/registration/capture', methods=['POST'])
def capture_photo():
    user_id = request.form.get('user_id')
    distance = request.form.get('distance')
    expression = request.form.get('expression')
    image_file = request.files.get('image')

    if not all([user_id, distance, expression, image_file]):
        return jsonify({'success': False, 'message': 'Data tidak lengkap.'}), 400

    paths = _get_user_dataset_paths(user_id)
    filename = f"{user_id}_{distance}m_{expression}.jpg"
    filepath = os.path.join(paths['input'], filename)
    image_file.save(filepath)

    return jsonify({'success': True, 'filename': filename})


@registration_bp.route('/registration/process', methods=['POST'])
def process_registration():
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id tidak ditemukan.'}), 400

    paths = _get_user_dataset_paths(user_id)
    input_files = sorted(os.listdir(paths['input']))

    if not input_files:
        return jsonify({'success': False, 'message': 'Belum ada foto yang diambil.'}), 400

    processed_faces = []                                     
    failed_files = []

    for filename in input_files:
        filepath = os.path.join(paths['input'], filename)
        frame = cv2.imread(filepath)
        if frame is None:
            failed_files.append(filename)
            continue

                                       
        faces = detector.detect(frame)
        if not faces:
            failed_files.append(filename)
            continue

                                                                           
                                                           
        face = max(faces, key=lambda f: f['confidence'])
        box = face['box']
        box_size = detector.get_box_size(box)

                                                                         
                                                                           
        mtcnn_vis = frame.copy()
        x, y, w, h = box
        cv2.rectangle(mtcnn_vis, (x, y), (x + w, y + h), (0, 255, 0), 2)

                                                                         
                                             
        keypoints = face['keypoints']
        landmark_color = (0, 0, 255)
        for point_name, (px, py) in keypoints.items():
            cv2.circle(mtcnn_vis, (int(px), int(py)), 3, landmark_color, -1)

        cv2.imwrite(os.path.join(paths['mtcnn_output'], filename), mtcnn_vis)

                           
        aligned_frame = detector.align_face(frame, face['keypoints'])
                                                         
        aligned_crop = detector.crop_face(aligned_frame, box)
        cv2.imwrite(os.path.join(paths['aligned'], filename), aligned_crop)

        if aligned_crop.size == 0:
            failed_files.append(filename)
            continue

                                                                                       
                                                       
        enhanced_rgb = enhancer.process(aligned_crop, box_size)

                                                                                   
        enhanced_bgr = cv2.cvtColor(enhanced_rgb, cv2.COLOR_RGB2BGR)
        cv2.imwrite(os.path.join(paths['enhanced'], filename), enhanced_bgr)

        processed_faces.append(enhanced_rgb)

    if not processed_faces:
                                                                          
                                                                          
                                       
        if os.path.exists(os.path.join(Config.DATASET_FOLDER, str(user_id))):
            shutil.rmtree(os.path.join(Config.DATASET_FOLDER, str(user_id)))
        return jsonify({
            'success': False,
            'message': 'Tidak ada wajah yang berhasil diproses dari seluruh foto. Registrasi dibatalkan otomatis.'
        }), 400

                                                                  
    embeddings = extractor.extract_batch(processed_faces)

                                                               
    avg_embedding = extractor.average_embedding(embeddings)

                                                                         
                                                                    
    nama_path = os.path.join(Config.DATASET_FOLDER, str(user_id), '_nama.txt')
    nama = 'Tanpa Nama'
    if os.path.exists(nama_path):
        with open(nama_path, 'r', encoding='utf-8') as f:
            nama = f.read().strip()

    UserModel.create(user_id, nama)
    EmbeddingModel.save(user_id, avg_embedding)

                                                                     
    if os.path.exists(nama_path):
        os.remove(nama_path)

                                                                            
    embedding_cache.refresh()

    return jsonify({
        'success': True,
        'message': 'Registrasi berhasil. Data user dan wajah telah tersimpan.',
        'total_foto': len(input_files),
        'foto_berhasil': len(processed_faces),
        'foto_gagal': len(failed_files),
        'gagal_list': failed_files
    })
