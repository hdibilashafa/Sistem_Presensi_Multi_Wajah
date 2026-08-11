/**
 * presence.js - Logika halaman Presensi:
 * mulai sesi -> kirim frame berulang ke /presence/frame -> gambar
 * bounding box hijau (dikenali) / merah (unknown) di atas video.
 *
 * Perbaikan performa & akurasi (revisi):
 * 1. Canvas overlay & capture-canvas SELALU disamakan ukurannya dengan
 *    resolusi asli video (videoWidth/videoHeight), bukan ukuran tampilan
 *    CSS, sehingga koordinat bounding box dari server pas dengan posisi
 *    wajah di layar (sebelumnya box "ngaco" karena ada mismatch skala).
 * 2. Pengiriman frame TIDAK pakai setInterval murni (yang bisa menumpuk
 *    request kalau respons server lambat), tapi pakai self-scheduling
 *    loop: frame berikutnya baru dikirim SETELAH respons frame
 *    sebelumnya diterima. Ini menghilangkan efek patah-patah/menumpuk.
 */

document.addEventListener('DOMContentLoaded', () => {
    const btnStartSession = document.getElementById('btn-start-session');
    const btnStopSession = document.getElementById('btn-stop-session');
    const sessionStatus = document.getElementById('session-status');
    const videoEl = document.getElementById('camera-feed');
    const overlayCanvas = document.getElementById('overlay-canvas');
    const captureCanvas = document.getElementById('capture-canvas');
    const detectionList = document.getElementById('detection-list');
    const overlayCtx = overlayCanvas.getContext('2d');

    let isSessionActive = false;
    let frameLoopTimeout = null;

    const FRAME_DELAY_MS = 150; // jeda antar frame SETELAH respons diterima

    btnStartSession.addEventListener('click', async () => {
        const cameraReady = await CameraModule.start('camera-feed');
        if (!cameraReady) return;

        // Tunggu metadata video siap supaya videoWidth/videoHeight valid
        await waitForVideoReady();
        syncCanvasSizeToVideo();

        const res = await fetch('/presence/start', { method: 'POST' });
        const data = await res.json();

        if (!data.success) {
            showToast('Gagal memulai sesi presensi.', 'error');
            return;
        }

        isSessionActive = true;
        sessionStatus.textContent = `Sesi aktif - ${data.total_user_terdaftar} user terdaftar (threshold: ${data.threshold})`;
        sessionStatus.className = 'badge badge-success';

        btnStartSession.disabled = true;
        btnStopSession.disabled = false;

        frameLoop(); // mulai self-scheduling loop
    });

    btnStopSession.addEventListener('click', async () => {
        isSessionActive = false;
        clearTimeout(frameLoopTimeout);

        const res = await fetch('/presence/stop', { method: 'POST' });
        const data = await res.json();

        CameraModule.stop();
        overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

        sessionStatus.textContent = 'Sesi dihentikan';
        sessionStatus.className = 'badge badge-neutral';

        btnStartSession.disabled = false;
        btnStopSession.disabled = true;

        showToast(`Sesi selesai. ${data.total_tercatat} user tercatat presensi.`);
    });

    function waitForVideoReady() {
        return new Promise((resolve) => {
            if (videoEl.videoWidth > 0) {
                resolve();
            } else {
                videoEl.addEventListener('loadedmetadata', () => resolve(), { once: true });
            }
        });
    }

    /**
     * Menyamakan resolusi INTERNAL canvas (overlay & capture) persis
     * dengan resolusi asli video dari kamera. Ukuran tampilan di layar
     * (CSS width:100%) tetap fleksibel, tapi koordinat gambar yang
     * dikembalikan server selalu cocok 1:1 dengan sistem koordinat canvas.
     */
    function syncCanvasSizeToVideo() {
        const w = videoEl.videoWidth;
        const h = videoEl.videoHeight;
        overlayCanvas.width = w;
        overlayCanvas.height = h;
        captureCanvas.width = w;
        captureCanvas.height = h;
    }

    /**
     * Self-scheduling loop: kirim 1 frame, tunggu hasilnya, gambar,
     * baru jadwalkan frame berikutnya. Mencegah penumpukan request
     * yang menyebabkan tampilan terasa patah-patah/lag menumpuk.
     */
    async function frameLoop() {
        if (!isSessionActive) return;

        try {
            await sendFrame();
        } catch (err) {
            console.error('Gagal memproses frame:', err);
        }

        frameLoopTimeout = setTimeout(frameLoop, FRAME_DELAY_MS);
    }

    async function sendFrame() {
        const imageBase64 = CameraModule.captureFrameBase64('capture-canvas');

        const res = await fetch('/presence/frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imageBase64 })
        });
        const data = await res.json();

        if (data.success) {
            drawDetections(data.faces);
            updateDetectionList(data.faces);
        }
    }

    /**
     * Menggambar bounding box di atas video. Karena overlayCanvas.width/height
     * sudah disamakan persis dengan videoWidth/videoHeight (lihat syncCanvasSizeToVideo),
     * koordinat (x, y, w, h) dari server bisa langsung digambar tanpa perlu
     * konversi skala tambahan -- inilah yang memperbaiki posisi box yang
     * sebelumnya meleset dari wajah.
     */
    function drawDetections(faces) {
        overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

        faces.forEach(face => {
            const { x, y, w, h } = face.box;
            const color = face.recognized ? '#1FA971' : '#E0473F';
            const label = face.recognized ? `${face.nama} (${(face.similarity * 100).toFixed(1)}%)` : 'Unknown';

            overlayCtx.strokeStyle = color;
            overlayCtx.lineWidth = 3;
            overlayCtx.strokeRect(x, y, w, h);

            overlayCtx.font = '14px Inter, sans-serif';
            overlayCtx.fillStyle = color;
            const textWidth = overlayCtx.measureText(label).width + 12;
            const labelY = y - 24 >= 0 ? y - 24 : y;
            overlayCtx.fillRect(x, labelY, textWidth, 24);

            overlayCtx.fillStyle = '#FFFFFF';
            overlayCtx.fillText(label, x + 6, labelY + 17);
        });
    }

    function updateDetectionList(faces) {
        if (faces.length === 0) {
            detectionList.innerHTML = '<p class="text-muted">Tidak ada wajah terdeteksi pada frame ini.</p>';
            return;
        }

        const rows = faces.map(f => `
            <div class="flex-between" style="padding:8px 0; border-bottom:1px solid var(--gray-200);">
                <span>${f.recognized ? f.nama : 'Unknown'}</span>
                <span class="badge ${f.recognized ? 'badge-success' : 'badge-danger'}">
                    ${(f.similarity * 100).toFixed(2)}%
                </span>
            </div>
        `).join('');

        detectionList.innerHTML = rows;
    }
});
