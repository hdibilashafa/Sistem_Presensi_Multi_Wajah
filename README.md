# FaceAttend: Sistem Presensi Berbasis Multi Face Recognition

![Python](https://img.shields.io/badge/Python-3.8--3.11-blue)
![Flask](https://img.shields.io/badge/Flask-Web_App-black)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.12-orange)
![MySQL](https://img.shields.io/badge/MySQL-Database-4479A1)

Sistem presensi berbasis web yang mampu **mendeteksi dan mengenali lebih dari satu wajah secara bersamaan** pada jarak hingga **2,5 meter**, dan berjalan hanya dengan CPU (tanpa GPU).

> Proyek Tugas Akhir (Skripsi) Teknik Informatika, Universitas Komputer Indonesia (UNIKOM).

---

## Fitur Utama

- **Multi-face recognition**: beberapa wajah dikenali sekaligus dalam satu frame
- **Registrasi terpandu**: 63 foto per user (9 jarak × 7 ekspresi) dengan hitung mundur otomatis
- **Presensi real time**: kotak hijau untuk wajah dikenali, kotak merah "Unknown" untuk wajah tidak dikenali
- **Satu presensi per hari** untuk setiap user
- **Evaluasi ROC**: analisis AUC dan penentuan threshold optimal (Youden's Index) langsung dari aplikasi
- **Laporan & ekspor CSV** dengan filter rentang tanggal
- **Tampilan Admin dan User terpisah**
- **CPU only**, tidak membutuhkan GPU

---

## Arsitektur Pipeline

```
Kamera → MTCNN (deteksi) → Face Alignment → Image Enhancement
       → ResNet-50 VGGFace2 (ekstraksi fitur) → Cosine Similarity → Presensi
```

| Tahap | Metode |
|---|---|
| Deteksi wajah | MTCNN |
| Alignment | Berdasarkan landmark MTCNN |
| Enhancement | Bicubic + CLAHE + Unsharp Masking |
| Ekstraksi fitur | ResNet-50 pretrained VGGFace2 |
| Pencocokan identitas | Cosine Similarity |

---

## Tech Stack

Python · Flask · TensorFlow/Keras · MTCNN · keras-vggface · MySQL · OpenCV · HTML/CSS/JS (Jinja2)

---

## Performa

Diuji pada CPU AMD Ryzen 5 5600H tanpa GPU:

| Kondisi | Waktu proses per frame |
|---|---|
| 1 wajah | ± 0,3 – 1 detik |
| 3–5 wajah | ± 1 – 3 detik |

---

## Instalasi

### Prasyarat

- Anaconda
- MySQL (XAMPP / MySQL Workbench / service Windows)

### 1. Clone repository dan siapkan environment

```bash
git clone https://github.com/USERNAME/NAMA-REPO.git
cd NAMA-REPO
conda activate nama_environment
conda install -c conda-forge tensorflow=2.12 keras=2.12 numpy=1.23 -y
pip install -r requirements.txt
```

> Jika `mysqlclient` gagal di-install di Windows: `conda install -c conda-forge mysqlclient -y`

### 2. Siapkan database

Jalankan skema database di MySQL:

```sql
SOURCE database/schema.sql;
```

Atau copy-paste isi `database/schema.sql` ke MySQL Workbench lalu Execute. Setelah itu sesuaikan kredensial di `config.py`:

```python
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = ''   # isi sesuai password MySQL
MYSQL_DB = 'face_recognition_db'
```

### 3. Jalankan aplikasi

```bash
python app.py
```

Buka `http://localhost:5000`.

> Saat pertama kali dijalankan, bobot pretrained VGGFace2 (± 90–150 MB) akan diunduh otomatis. Pastikan terhubung ke internet.

---

## Cara Penggunaan

| Peran | URL | Fungsi |
|---|---|---|
| Admin | `/admin/dashboard` | Registrasi user, sesi presensi, evaluasi ROC, laporan |
| User | `/` atau `/status` | Melihat dan mengekspor riwayat kehadiran pribadi |

> Pemisahan admin/user hanya di level tampilan (belum ada sistem login), sehingga URL admin tetap dapat diakses jika diketik manual.

<details>
<summary><b>Registrasi user baru (Admin)</b></summary>

1. Buka menu **Data User** → **+ Registrasi User Baru**
2. Masukkan **ID (8 digit angka, contoh: 20240001)** dan **Nama**, lalu klik **Mulai Registrasi**
3. Izinkan akses kamera pada browser
4. Untuk setiap kombinasi jarak dan ekspresi yang muncul, tekan **"Tekan untuk Mulai"** atau tombol **S**. Hitung mundur 3-2-1 berjalan otomatis dan foto langsung diambil
5. Ulangi hingga 63 foto selesai (9 jarak × 7 ekspresi)
6. Untuk membatalkan, klik **Batalkan Registrasi** (seluruh data dan foto yang sudah diambil akan dihapus)
7. Setelah selesai, sistem memproses foto secara otomatis: deteksi → alignment → enhancement → ekstraksi → rata-rata embedding → simpan ke database

</details>

<details>
<summary><b>Menjalankan sesi presensi (Admin)</b></summary>

1. Buka menu **Presensi**
2. Klik **Mulai Sesi Presensi** dan izinkan kamera
3. Sistem mendeteksi dan mengenali wajah secara berkelanjutan
4. Kotak **hijau** berarti dikenali, kotak **merah "Unknown"** berarti tidak dikenali
5. Setiap user hanya tercatat **sekali per hari**
6. Klik **Hentikan Sesi** untuk selesai

</details>

<details>
<summary><b>Evaluasi ROC dan penentuan threshold</b></summary>

1. Lakukan pengujian manual: catat skor similarity untuk pasangan wajah **genuine** (seharusnya cocok) dan **impostor** (seharusnya tidak cocok)
2. Buka menu **Evaluasi ROC** dan masukkan setiap skor
3. Klik **Jalankan Analisis** untuk melihat kurva ROC, AUC, dan threshold optimal
4. Klik **Terapkan Threshold** untuk langsung memakainya di sistem

</details>

<details>
<summary><b>Laporan dan status kehadiran</b></summary>

- **Laporan** (admin, `/admin/report`): filter rentang tanggal dan ekspor `.csv`
- **Status Kehadiran** (user, `/status`): cari nama/ID lewat kotak pencarian, lihat dan ekspor riwayat kehadiran pribadi

</details>

---

## Struktur Project

```
face_recognition_sistem/
├── app.py                  # entry point Flask
├── config.py               # konfigurasi sistem
├── requirements.txt
├── database/
│   ├── schema.sql          # struktur tabel MySQL
│   └── models.py           # query database
├── core/
│   ├── detector.py         # MTCNN: deteksi wajah + face alignment
│   ├── enhancer.py         # bicubic + CLAHE + unsharp masking
│   ├── extractor.py        # ResNet-50 VGGFace2: ekstraksi fitur
│   ├── matcher.py          # Cosine Similarity
│   └── embedding_cache.py  # cache embedding di memori
├── routes/
│   ├── registration.py     # alur registrasi
│   ├── presence.py         # presensi real time
│   ├── admin.py            # dashboard, kelola user, laporan
│   ├── user.py             # status kehadiran pribadi
│   └── evaluation.py       # analisis ROC
├── evaluation/
│   ├── roc_analysis.py     # TPR/FPR/AUC/Youden's Index
│   └── results/            # ground truth dan grafik ROC
├── dataset/                # foto per user per tahap pemrosesan
├── templates/              # HTML (Jinja2)
└── static/
    ├── css/main.css
    └── js/
```

<details>
<summary>Struktur folder dataset per user</summary>

```
dataset/{user_id}/
├── input/          # foto asli hasil capture kamera
├── mtcnn_output/   # foto dengan bounding box hasil MTCNN
├── aligned/        # hasil crop setelah face alignment
└── enhanced/       # hasil akhir enhancement (siap diekstrak)
```

</details>

---

## Troubleshooting

| Masalah | Solusi |
|---|---|
| `ModuleNotFoundError: mtcnn` | `pip install mtcnn` di environment yang aktif |
| Error koneksi MySQL | Cek `config.py` dan pastikan service MySQL berjalan |
| Kamera tidak muncul di browser | Akses lewat `localhost` (bukan IP) dan izinkan permission kamera |
| Model VGGFace2 gagal diunduh | Cek koneksi internet, atau unduh manual sesuai dokumentasi `keras-vggface` |
| `ModuleNotFoundError: keras.engine.topology` | Jalankan `python fix_keras_vggface.py` |
| Presensi lambat / patah-patah | Lihat bagian optimasi di bawah |

<details>
<summary><b>Optimasi performa (CPU only)</b></summary>

Sudah diterapkan secara default:

- `DEBUG = False` di `config.py`
- TensorFlow memakai seluruh core CPU yang tersedia
- Flask berjalan dengan `threaded=True`
- Model dipanaskan (warm-up) sekali saat aplikasi start, memakai pemanggilan model langsung dan `float32` untuk inferensi real time

Jika masih lambat:

1. Pastikan `DEBUG = False` lalu jalankan ulang `python app.py`
2. Tutup aplikasi berat lain yang memakai CPU
3. Naikkan `FRAME_DELAY_MS` di `static/js/presence.js` (misal dari `150` ke `500`)
4. Untuk performa jauh lebih baik, gunakan GPU NVIDIA + `tensorflow-gpu` (di luar cakupan penelitian CPU-only ini)

</details>

---

## Keterbatasan

- Belum ada sistem autentikasi login
- Ekstraksi fitur dipanggil per wajah, sehingga waktu proses naik seiring jumlah wajah
- Belum diuji terhadap serangan spoofing (foto/video)

---

## Author

**Nabilah Shafa**
Teknik Informatika, Universitas Komputer Indonesia (UNIKOM)
