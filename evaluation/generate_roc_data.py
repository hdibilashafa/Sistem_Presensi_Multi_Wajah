
import os
import sys
import json
import cv2

                                                                         
                                                              
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database.models import EmbeddingModel
from core.detector import FaceDetector
from core.enhancer import ImageEnhancer
from core.extractor import FeatureExtractor
from core.matcher import FaceMatcher

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_PHOTOS_DIR = os.path.join(SCRIPT_DIR, 'test_photos')
SCORES_PATH = os.path.join(SCRIPT_DIR, 'results', 'scores.json')


def load_scores():
    if not os.path.exists(SCORES_PATH):
        return {'genuine': [], 'impostor': []}
    with open(SCORES_PATH, 'r') as f:
        return json.load(f)


def save_scores(data):
    os.makedirs(os.path.dirname(SCORES_PATH), exist_ok=True)
    with open(SCORES_PATH, 'w') as f:
        json.dump(data, f)


def main():
    if not os.path.isdir(TEST_PHOTOS_DIR):
        print(f"[ERROR] Folder tidak ditemukan: {TEST_PHOTOS_DIR}")
        print("Buat dulu foldernya, isi subfolder per orang. Contoh:")
        print("  evaluation/test_photos/10122229/foto1.jpg")
        print("  evaluation/test_photos/unregistered_01/foto1.jpg")
        return

    app = create_app()
    with app.app_context():
        reference_embeddings = EmbeddingModel.get_all()                                          

    if not reference_embeddings:
        print("[ERROR] Belum ada embedding referensi di database. Registrasi user dulu lewat web.")
        return

    print(f"[INFO] {len(reference_embeddings)} user referensi ditemukan di database:")
    for uid, data in reference_embeddings.items():
        print(f"       - {uid} ({data['nama']})")

    detector = FaceDetector()
    enhancer = ImageEnhancer()
    extractor = FeatureExtractor()

    scores = load_scores()
    total_genuine_added = 0
    total_impostor_added = 0
    total_photo_diproses = 0
    total_gagal_deteksi = 0

    person_folders = sorted(os.listdir(TEST_PHOTOS_DIR))

    for person_label in person_folders:
        person_dir = os.path.join(TEST_PHOTOS_DIR, person_label)
        if not os.path.isdir(person_dir):
            continue

        true_user_id = person_label if person_label in reference_embeddings else None
        if true_user_id:
            print(f"\n[INFO] Folder '{person_label}' -> TERDAFTAR sebagai {reference_embeddings[true_user_id]['nama']}")
        else:
            print(f"\n[INFO] Folder '{person_label}' -> TIDAK TERDAFTAR (semua hasil = impostor)")

        photo_files = [f for f in sorted(os.listdir(person_dir))
                       if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        if not photo_files:
            print(f"  [SKIP] Tidak ada foto di folder ini.")
            continue

        for photo_file in photo_files:
            photo_path = os.path.join(person_dir, photo_file)
            frame = cv2.imread(photo_path)
            if frame is None:
                print(f"  [SKIP] Gagal membaca file: {photo_file}")
                continue

            faces = detector.detect(frame)
            if len(faces) == 0:
                print(f"  [SKIP] Tidak ada wajah terdeteksi: {photo_file}")
                total_gagal_deteksi += 1
                continue

                                                                                            
            face = max(faces, key=lambda f: f['confidence'])
            box = face['box']
            box_size = detector.get_box_size(box)

            aligned_frame = detector.align_face(frame, face['keypoints'])
            aligned_crop = detector.crop_face(aligned_frame, box)
            if aligned_crop.size == 0:
                print(f"  [SKIP] Hasil crop kosong: {photo_file}")
                continue

            enhanced_rgb = enhancer.process(aligned_crop, box_size)
            embedding = extractor.extract(enhanced_rgb)
            total_photo_diproses += 1

            for ref_user_id, ref_data in reference_embeddings.items():
                score = round(float(FaceMatcher.cosine_similarity(embedding, ref_data['embedding'])), 4)

                if true_user_id is not None and ref_user_id == true_user_id:
                    scores['genuine'].append(score)
                    total_genuine_added += 1
                    label = 'GENUINE'
                else:
                    scores['impostor'].append(score)
                    total_impostor_added += 1
                    label = 'impostor'

                print(f"    {photo_file}  vs  {ref_user_id} ({ref_data['nama']})  ->  {score:.4f}  [{label}]")

    save_scores(scores)

    print("\n" + "=" * 50)
    print("[SELESAI]")
    print(f"Foto berhasil diproses  : {total_photo_diproses}")
    print(f"Foto gagal deteksi      : {total_gagal_deteksi}")
    print(f"Skor genuine ditambah   : {total_genuine_added}")
    print(f"Skor impostor ditambah  : {total_impostor_added}")
    print(f"Total genuine sekarang  : {len(scores['genuine'])}")
    print(f"Total impostor sekarang : {len(scores['impostor'])}")
    print(f"Tersimpan ke: {SCORES_PATH}")
    print("\nBuka halaman Evaluasi ROC di browser, lalu klik 'Jalankan Analisis'.")


if __name__ == '__main__':
    main()
