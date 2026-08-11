# Sistem Presensi Berbasis Multi Face Recognition

Sistem presensi yang mampu mendeteksi dan mengenali lebih dari satu wajah
secara bersamaan pada jarak 2,5 meter, menggunakan MTCNN (deteksi wajah),
ResNet-50 *pretrained* VGGFace2 (ekstraksi fitur), dan Cosine Similarity
(pencocokan identitas).

---

## 1. Persiapan Environment (Anaconda)

Buka **Anaconda Prompt**, lalu jalankan:

```bash
# Aktifkan environment khusus project ini (sesuaikan nama env-mu)
conda activate nama_environment_kamu

# Masuk ke folder project
cd path\ke\face_recognition_sistem
```

### Install library inti via conda (lebih stabil di Windows)

```bash
conda install -c conda-forge tensorflow=2.12 keras=2.12 numpy=1.23 -y
```

### Install sisanya via pip (di dalam environment yang sama)

```bash
pip install -r requirements.txt
```

> **Catatan:** Jika `mysqlclient` gagal di-install lewat pip di Windows,
> gunakan cara alternatif:
> ```bash
> conda install -c conda-forge mysqlclient -y
> ```

---

## 2. Persiapan Database (MySQL)

Pastikan MySQL sudah berjalan (lewat XAMPP / MySQL Workbench / service Windows).

Buka MySQL (lewat terminal `mysql -u root -p` atau MySQL Workbench), lalu jalankan:

```sql
SOURCE path/ke/face_recognition_sistem/database/schema.sql;
```

Atau cukup copy-paste isi file `database/schema.sql` ke MySQL Workbench
dan jalankan (Execute).

### Sesuaikan koneksi database

Buka `config.py`, sesuaikan bagian ini dengan kredensial MySQL kamu:

```python
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = ''   # isi sesuai password MySQL kamu
MYSQL_DB = 'face_recognition_db'
```

---

## 3. Download Model Pretrained (Otomatis)

Saat pertama kali dijalankan, `keras-vggface` akan otomatis mengunduh
bobot pretrained ResNet-50 VGGFace2 (sekitar 90-150 MB). Pastikan
laptop terhubung internet saat pertama kali menjalankan aplikasi.

---

## 4. Menjalankan Aplikasi

```bash
python app.py
```

Jika berhasil, akan muncul:

```
[INFO] Embedding cache dimuat: 0 user.
 * Running on http://0.0.0.0:5000
```

Buka browser, akses:

```
http://localhost:5000
```

---

## 5. Alur Penggunaan

### Akses Admin vs User (Terpisah)

- **Admin**: akses langsung lewat `http://localhost:5000/admin/dashboard`
- **User**: akses lewat `http://localhost:5000/` (halaman utama otomatis ke Status Kehadiran)

Sidebar admin dan user terpisah total -- user tidak melihat menu admin sama sekali (dan sebaliknya), sesuai kebutuhan pemisahan akses. Catatan: pemisahan ini di level tampilan/menu saja (tanpa sistem login), jadi URL admin tetap bisa diakses langsung jika diketik manual.

### a. Registrasi User Baru (khusus Admin)
1. Buka menu **Data User** > **+ Registrasi User Baru**
2. Masukkan **ID (8 digit angka, contoh: 20240001)** dan **Nama**, klik **Mulai Registrasi**
3. Izinkan akses kamera pada browser
4. Untuk setiap kombinasi jarak & ekspresi yang muncul (lengkap dengan panduan ikon & deskripsi ekspresi), tekan tombol **"Tekan untuk Mulai"** atau tombol keyboard **S** -> hitung mundur 3-2-1 otomatis -> foto otomatis terambil
5. Ulangi hingga 63 foto selesai (9 jarak x 7 ekspresi)
6. Jika perlu membatalkan di tengah jalan, klik **Batalkan Registrasi** -- seluruh data & foto yang sudah diambil akan dihapus
7. Setelah selesai, sistem otomatis memproses seluruh foto (deteksi -> alignment -> enhancement -> ekstraksi -> rata-rata embedding -> simpan ke database)

### b. Presensi (khusus Admin menjalankan sesi)
1. Buka menu **Presensi**
2. Klik **Mulai Sesi Presensi**, izinkan kamera
3. Sistem otomatis mendeteksi & mengenali wajah secara berkelanjutan (bounding box mengikuti posisi wajah secara akurat dan halus)
4. Kotak **hijau** = dikenali, kotak **merah "Unknown"** = tidak dikenali
5. **Setiap user hanya tercatat presensi SEKALI per hari** -- jika wajah yang sama terdeteksi berkali-kali di hari yang sama, hanya presensi pertama yang tersimpan ke database
6. Klik **Hentikan Sesi** untuk selesai

### c. Evaluasi & Penentuan Threshold (ROC)
1. Lakukan pengujian manual: catat similarity score untuk pasangan wajah yang **seharusnya cocok** (genuine) dan **seharusnya tidak cocok** (impostor)
2. Buka menu **Evaluasi ROC**, masukkan setiap skor sebagai genuine/impostor
3. Klik **Jalankan Analisis** untuk melihat kurva ROC, AUC, dan threshold optimal
4. Klik **Terapkan Threshold** untuk langsung memakai nilai tersebut di sistem

### d. Laporan (Admin) & Status Kehadiran (User)
- **Laporan** (admin, di `/admin/report`): filter rentang tanggal, ekspor `.csv`
- **Status Kehadiran** (user, di `/status`): cari nama/ID lewat kotak pencarian (bukan dropdown), lihat & ekspor riwayat kehadiran pribadi

---

## 6. Struktur Folder Dataset

Setiap user yang registrasi otomatis memiliki folder berikut, agar
proses tiap tahap bisa diperiksa secara visual:

```
dataset/
└── {user_id}/
    ├── input/           -> foto asli hasil capture kamera
    ├── mtcnn_output/    -> foto dengan bounding box hasil deteksi MTCNN
    ├── aligned/         -> hasil crop setelah face alignment
    └── enhanced/        -> hasil akhir setelah image enhancement (siap diekstrak)
```

---

## 7. Struktur Project

```
face_recognition_sistem/
├── app.py                  # entry point Flask
├── config.py                # semua konfigurasi sistem
├── requirements.txt
├── database/
│   ├── schema.sql            # struktur tabel MySQL
│   └── models.py              # query database (UserModel, EmbeddingModel, dst)
├── core/
│   ├── detector.py            # MTCNN: deteksi wajah + face alignment
│   ├── enhancer.py            # bicubic + CLAHE + unsharp masking
│   ├── extractor.py           # ResNet-50 VGGFace2: ekstraksi fitur
│   ├── matcher.py              # Cosine Similarity
│   └── embedding_cache.py     # cache embedding di memori (bukan query DB tiap frame)
├── routes/
│   ├── registration.py        # alur registrasi
│   ├── presence.py            # alur presensi real time
│   ├── admin.py                 # dashboard, kelola user, laporan
│   ├── user.py                  # status kehadiran pribadi
│   └── evaluation.py           # analisis ROC
├── evaluation/
│   ├── roc_analysis.py        # perhitungan TPR/FPR/AUC/Youden's Index
│   └── results/                  # data ground truth & grafik ROC tersimpan di sini
├── dataset/                     # foto per user, per tahap pemrosesan
├── templates/                   # HTML (Jinja2)
└── static/
    ├── css/main.css            # tema navy + putih
    └── js/                       # camera.js, registration.js, presence.js, dst
```

---

## 8. Troubleshooting

| Masalah | Solusi |
|---|---|
| `ModuleNotFoundError: mtcnn` | `pip install mtcnn` di environment yang aktif |
| Error koneksi MySQL | Cek `config.py`, pastikan MySQL service berjalan |
| Kamera tidak muncul di browser | Pastikan mengakses lewat `localhost` (bukan IP), izinkan permission kamera |
| Model VGGFace2 gagal diunduh | Cek koneksi internet, atau unduh manual sesuai dokumentasi `keras-vggface` |
| `ModuleNotFoundError: keras.engine.topology` (dari dalam keras_vggface) | Jalankan `python fix_keras_vggface.py` untuk memperbaiki otomatis |
| Presensi terasa patah-patah / lambat (3+ detik per wajah) | Lihat bagian "Optimasi Performa Presensi" di bawah |

### Optimasi Performa Presensi (CPU only, tanpa GPU)

Sudah diterapkan secara default di sistem ini:
- `DEBUG = False` di `config.py` -- mode debug Flask menambah overhead besar di setiap request, dimatikan secara default
- TensorFlow dikonfigurasi memakai seluruh core CPU yang tersedia (`app.py`)
- Flask dijalankan dengan `threaded=True` -- mencegah request menumpuk/mengantre
- `FeatureExtractor` melakukan "pemanasan" model sekali saat aplikasi start, dan memakai pemanggilan model langsung (bukan `.predict()`) serta `float32` untuk inferensi real time -- jauh lebih cepat dibanding `.predict()` + `float64` untuk kasus 1 gambar per panggilan

**Ekspektasi waktu wajar setelah optimasi** (CPU seperti AMD Ryzen 5 5600H, tanpa GPU):
- 1 wajah per frame: sekitar 0.3 - 1 detik
- 3-5 wajah per frame: sekitar 1 - 3 detik (karena ekstraksi fitur ResNet-50 tetap dipanggil satu per satu per wajah yang terdeteksi)

Jika masih terasa lambat setelah update ini:
1. Pastikan `config.py` sudah `DEBUG = False` dan jalankan ulang `python app.py`
2. Pastikan tidak ada aplikasi berat lain (browser tab banyak, aplikasi lain) yang ikut memakai CPU
3. Di `static/js/presence.js`, nilai `FRAME_DELAY_MS = 150` bisa dinaikkan (misal ke `500`) agar jeda antar frame lebih longgar dan beban CPU tidak menumpuk terus-menerus
4. Untuk performa terbaik secara signifikan, pertimbangkan menjalankan di perangkat dengan GPU NVIDIA + `tensorflow-gpu`, meskipun ini di luar cakupan skripsi yang menguji performa CPU-only
