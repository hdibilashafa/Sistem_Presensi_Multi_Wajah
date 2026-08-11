/**
 * registration.js - Logika halaman Registrasi:
 * form identitas (ID 8 digit + nama) -> kamera aktif -> capture 63 foto
 * (9 jarak x 7 ekspresi).
 *
 * Alur capture (revisi):
 * - Foto dikelompokkan PER JARAK. User pindah posisi ke jarak tertentu,
 *   lalu tekan tombol/tombol S SEKALI untuk memulai jarak tersebut.
 * - Begitu dimulai, sistem otomatis berjalan melalui 7 ekspresi secara
 *   berturut-turut TANPA perlu menekan S lagi: setiap ekspresi diawali
 *   countdown 3-2-1 (supaya user tidak terburu-buru menyiapkan
 *   ekspresi wajahnya), lalu otomatis capture, lalu lanjut ke
 *   ekspresi berikutnya dengan countdown lagi, dst.
 * - Setelah 7 ekspresi pada jarak itu selesai, sistem BERHENTI dan
 *   menunggu user pindah ke jarak berikutnya lalu menekan S lagi.
 *
 * Tombol "Batalkan Registrasi" menghapus user & seluruh foto yang
 * sudah sempat diambil.
 */

document.addEventListener('DOMContentLoaded', () => {
    const { distances, expressions, totalPhotos } = window.REGISTRATION_CONFIG;

    const stepIdentity = document.getElementById('step-identity');
    const stepCapture = document.getElementById('step-capture');
    const stepResult = document.getElementById('step-result');

    const inputId = document.getElementById('input-id');
    const inputNama = document.getElementById('input-nama');
    const btnStart = document.getElementById('btn-start');
    const btnCapture = document.getElementById('btn-capture');
    const btnCancel = document.getElementById('btn-cancel');

    const captureProgress = document.getElementById('capture-progress');
    const currentDistanceEl = document.getElementById('current-distance');
    const currentExpressionEl = document.getElementById('current-expression');
    const expressionIconEl = document.getElementById('expression-icon');
    const expressionHintEl = document.getElementById('expression-hint');
    const resultContent = document.getElementById('result-content');

    const countdownOverlay = document.getElementById('countdown-overlay');
    const countdownNumber = document.getElementById('countdown-number');

    let userId = null;

    // distanceGroups: array per jarak, masing-masing berisi list ekspresi
    // yang harus diambil berturut-turut untuk jarak tersebut.
    // Contoh: [{ distance: 1.00, expressions: ['netral', 'bahagia', ...] }, ...]
    let distanceGroups = [];
    let distanceIndex = 0;      // jarak ke berapa yang sedang aktif
    let expressionIndex = 0;    // ekspresi ke berapa DALAM jarak ini yang sedang diambil
    let totalCaptured = 0;      // total foto yang sudah berhasil diambil (untuk progress bar)

    let isRunningGroup = false; // true selama 1 kelompok jarak sedang berjalan otomatis

    // Panduan visual (emoji + deskripsi singkat) untuk tiap ekspresi,
    // sesuai 7 ekspresi dasar Paul Ekman yang dipakai pada penelitian ini.
    const EXPRESSION_GUIDE = {
        netral: { icon: '🙂', hint: 'Tatap kamera dengan wajah rileks, tanpa ekspresi berlebihan.' },
        bahagia: { icon: '😄', hint: 'Tersenyum lebar secara natural, seperti sedang senang.' },
        sedih: { icon: '😢', hint: 'Turunkan sudut mulut, tunjukkan raut wajah murung.' },
        marah: { icon: '😠', hint: 'Kerutkan alis, rahang sedikit mengencang.' },
        terkejut: { icon: '😲', hint: 'Buka mata dan mulut lebih lebar dari biasanya.' },
        jijik: { icon: '🤢', hint: 'Kerutkan hidung, sedikit tarik bibir atas ke atas.' },
        takut: { icon: '😨', hint: 'Buka mata lebar, alis terangkat, wajah tegang.' }
    };

    function buildDistanceGroups() {
        return distances.map(d => ({
            distance: d,
            expressions: [...expressions]
        }));
    }

    // ===== Step 1: Mulai registrasi =====
    btnStart.addEventListener('click', async () => {
        const userIdValue = inputId.value.trim();
        const nama = inputNama.value.trim();

        if (!/^[0-9]{8}$/.test(userIdValue)) {
            showToast('ID harus tepat 8 digit angka.', 'error');
            return;
        }
        if (!nama) {
            showToast('Nama tidak boleh kosong.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('user_id', userIdValue);
        formData.append('nama', nama);

        const res = await fetch('/registration/start', { method: 'POST', body: formData });
        const data = await res.json();

        if (!data.success) {
            showToast(data.message, 'error');
            return;
        }

        userId = data.user_id;
        distanceGroups = buildDistanceGroups();
        distanceIndex = 0;
        expressionIndex = 0;
        totalCaptured = 0;

        stepIdentity.style.display = 'none';
        stepCapture.style.display = 'block';

        const cameraReady = await CameraModule.start('camera-feed');
        if (!cameraReady) return;

        updateUIForNewDistance();
    });

    /**
     * Dipanggil setiap kali pindah ke jarak baru (atau di awal).
     * Menampilkan jarak yang harus dituju, ekspresi pertama sebagai
     * preview, dan menunggu user menekan tombol/S untuk memulai
     * seluruh rangkaian 7 ekspresi pada jarak ini.
     */
    function updateUIForNewDistance() {
        const group = distanceGroups[distanceIndex];
        currentDistanceEl.textContent = `${group.distance.toFixed(2)} m`;
        captureProgress.textContent = `${totalCaptured} / ${totalPhotos}`;

        showExpressionPreview(group.expressions[0]);

        btnCapture.disabled = false;
        btnCapture.textContent = `Mulai Jarak Ini (atau tombol S)`;
    }

    function showExpressionPreview(expressionName) {
        currentExpressionEl.textContent = expressionName;
        const guide = EXPRESSION_GUIDE[expressionName] || { icon: '🙂', hint: '' };
        expressionIconEl.textContent = guide.icon;
        expressionHintEl.textContent = guide.hint;
    }

    // ===== Tekan S / klik tombol -> mulai SELURUH rangkaian ekspresi untuk jarak ini =====
    btnCapture.addEventListener('click', startDistanceGroup);
    document.addEventListener('keydown', (e) => {
        if (stepCapture.style.display === 'none') return;
        if ((e.key === 's' || e.key === 'S') && !isRunningGroup) {
            startDistanceGroup();
        }
    });

    async function startDistanceGroup() {
        if (isRunningGroup || distanceIndex >= distanceGroups.length) return;
        isRunningGroup = true;
        expressionIndex = 0;
        btnCapture.disabled = true;
        btnCapture.textContent = 'Sedang berjalan...';

        await runNextExpressionInGroup();
    }

    /**
     * Loop internal: jalankan countdown -> capture untuk SATU ekspresi,
     * lalu otomatis lanjut ke ekspresi berikutnya dalam jarak yang sama
     * tanpa perlu input apapun dari user, sampai 7 ekspresi selesai.
     */
    async function runNextExpressionInGroup() {
        const group = distanceGroups[distanceIndex];

        if (expressionIndex >= group.expressions.length) {
            // Jarak ini selesai (7 ekspresi sudah diambil)
            isRunningGroup = false;
            distanceIndex++;

            if (distanceIndex >= distanceGroups.length) {
                await finishCapture();
            } else {
                updateUIForNewDistance(); // tunggu user tekan S lagi untuk jarak berikutnya
            }
            return;
        }

        const expressionName = group.expressions[expressionIndex];
        showExpressionPreview(expressionName);
        captureProgress.textContent = `${totalCaptured} / ${totalPhotos}`;

        await runCountdown();
        await doCapture(group.distance, expressionName);

        expressionIndex++;
        await runNextExpressionInGroup(); // lanjut otomatis ke ekspresi berikutnya
    }

    function runCountdown() {
        return new Promise((resolve) => {
            let count = 3;
            countdownOverlay.style.display = 'flex';
            countdownNumber.textContent = count;

            const countdownInterval = setInterval(() => {
                count -= 1;
                if (count > 0) {
                    countdownNumber.textContent = count;
                } else {
                    clearInterval(countdownInterval);
                    countdownOverlay.style.display = 'none';
                    resolve();
                }
            }, 1000);
        });
    }

    // ===== Ambil 1 foto dari frame video saat ini & kirim ke server =====
    async function doCapture(distance, expressionName) {
        const blob = await CameraModule.captureFrameBlob('capture-canvas');

        const formData = new FormData();
        formData.append('user_id', userId);
        formData.append('distance', distance.toFixed(2));
        formData.append('expression', expressionName);
        formData.append('image', blob, 'capture.jpg');

        const res = await fetch('/registration/capture', { method: 'POST', body: formData });
        const data = await res.json();

        if (!data.success) {
            showToast(data.message, 'error');
            return;
        }

        totalCaptured++;
        captureProgress.textContent = `${totalCaptured} / ${totalPhotos}`;
    }

    // ===== Step 3: Semua foto selesai diambil -> proses ke server =====
    async function finishCapture() {
        CameraModule.stop();
        stepCapture.style.display = 'none';
        stepResult.style.display = 'block';
        resultContent.innerHTML = `<p class="text-muted">Memproses ${totalPhotos} foto: deteksi wajah, image enhancement, ekstraksi fitur... Mohon tunggu.</p>`;

        const formData = new FormData();
        formData.append('user_id', userId);

        const res = await fetch('/registration/process', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.success) {
            resultContent.innerHTML = `
                <div class="alert alert-success">${data.message}</div>
                <p>Total foto diambil: <strong>${data.total_foto}</strong></p>
                <p>Berhasil diproses: <strong>${data.foto_berhasil}</strong></p>
                <p>Gagal diproses: <strong>${data.foto_gagal}</strong></p>
                <a href="/admin/users" class="btn btn-primary" style="margin-top:16px;">Kembali ke Data User</a>
            `;
        } else {
            resultContent.innerHTML = `<div class="alert alert-error">${data.message}</div>`;
        }
    }

    // ===== Batalkan registrasi =====
    btnCancel.addEventListener('click', async () => {
        if (!confirm('Batalkan registrasi? Seluruh foto yang sudah diambil akan dihapus.')) return;

        isRunningGroup = false;
        CameraModule.stop();

        if (userId) {
            const formData = new FormData();
            formData.append('user_id', userId);
            await fetch('/registration/cancel', { method: 'POST', body: formData });
        }

        showToast('Registrasi dibatalkan.');
        window.location.href = '/admin/users';
    });
});
