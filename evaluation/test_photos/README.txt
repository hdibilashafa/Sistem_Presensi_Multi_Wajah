Taruh foto uji BARU di sini (bukan foto registrasi), dikelompokkan per folder:

  test_photos/10122229/foto1.jpg      <- ID yang SUDAH terdaftar (nama folder = user_id di DB)
  test_photos/10122229/foto2.jpg
  test_photos/unregistered_01/foto1.jpg   <- orang yang TIDAK terdaftar (nama folder bebas)

Lalu jalankan dari root folder proyek:
  python evaluation/generate_roc_data.py
