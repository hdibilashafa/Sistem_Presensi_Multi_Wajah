
import os
import re
import importlib.util


def find_keras_vggface_path():
    spec = importlib.util.find_spec('keras_vggface')
    if spec is None or spec.submodule_search_locations is None:
        return None
    return list(spec.submodule_search_locations)[0]


                                               
REPLACEMENTS = [
    (
        r'from keras\.engine\.topology import get_source_inputs',
        'from tensorflow.keras.utils import get_source_inputs'
    ),
    (
        r'from keras\.engine import get_source_inputs',
        'from tensorflow.keras.utils import get_source_inputs'
    ),
    (
        r'from keras\.utils\.data_utils import get_file',
        'from tensorflow.keras.utils import get_file'
    ),
    (
        r'from keras\.utils import layer_utils',
        'from tensorflow.python.keras.utils import layer_utils'
    ),
    (
        r'from keras import backend as K',
        'from tensorflow.keras import backend as K'
    ),
    (
        r'from keras\.layers import',
        'from tensorflow.keras.layers import'
    ),
    (
        r'from keras\.models import',
        'from tensorflow.keras.models import'
    ),
    (
        r'from keras\.utils\.layer_utils import',
        'from tensorflow.python.keras.utils.layer_utils import'
    ),
    (
        r'import keras\.backend as K',
        'import tensorflow.keras.backend as K'
    ),
    (
        r'from keras_applications import',
        'from keras.applications import'                            
    ),
]


def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes_made = []

    for old_pattern, new_line in REPLACEMENTS:
        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_line, content)
            changes_made.append(f"  - {old_pattern}  ->  {new_line}")

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes_made

    return []


def main():
    print("=" * 60)
    print("Mencari lokasi instalasi keras_vggface...")
    print("=" * 60)

    base_path = find_keras_vggface_path()

    if base_path is None:
        print("\n[GAGAL] keras_vggface tidak ditemukan di environment ini.")
        print("Pastikan kamu sudah 'conda activate' environment yang benar")
        print("dan sudah menjalankan 'pip install keras-vggface'.")
        return

    print(f"\nDitemukan di: {base_path}\n")

    py_files = [
        os.path.join(base_path, f)
        for f in os.listdir(base_path)
        if f.endswith('.py')
    ]

    total_files_patched = 0

    for filepath in py_files:
        changes = patch_file(filepath)
        if changes:
            total_files_patched += 1
            print(f"[DIPERBAIKI] {os.path.basename(filepath)}")
            for c in changes:
                print(c)
            print()

    print("=" * 60)
    if total_files_patched > 0:
        print(f"Selesai. {total_files_patched} file berhasil diperbaiki.")
        print("Silakan jalankan ulang: python app.py")
    else:
        print("Tidak ada perubahan yang diperlukan (sudah kompatibel,")
        print("atau pola error berbeda dari yang sudah diketahui script ini).")
        print("Jika masih ada error ModuleNotFoundError lain, kirim pesan")
        print("error lengkapnya untuk ditambahkan ke script ini.")
    print("=" * 60)


if __name__ == '__main__':
    main()
