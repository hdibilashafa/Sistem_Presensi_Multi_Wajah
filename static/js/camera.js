/**
 * camera.js - Modul akses kamera laptop melalui browser (getUserMedia API).
 * Dipakai bersama oleh registration.js dan presence.js.
 */

const CameraModule = {
    stream: null,
    videoElement: null,

    /**
     * Mengaktifkan kamera dan menampilkannya ke elemen <video>.
     * @param {string} videoElementId - id elemen <video> di halaman
     * @param {object} constraints - resolusi yang diinginkan (default 1280x720 / HD)
     */
    async start(videoElementId, constraints = null) {
        this.videoElement = document.getElementById(videoElementId);

        const defaultConstraints = {
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            },
            audio: false
        };

        try {
            this.stream = await navigator.mediaDevices.getUserMedia(constraints || defaultConstraints);
            this.videoElement.srcObject = this.stream;
            return true;
        } catch (err) {
            console.error('Gagal mengakses kamera:', err);
            showToast('Gagal mengakses kamera. Periksa izin kamera pada browser.', 'error');
            return false;
        }
    },

    /**
     * Mengambil satu frame dari video saat ini dan mengembalikannya
     * sebagai Blob (file gambar) siap dikirim via FormData ke Flask.
     */
    captureFrame(canvasElementId) {
        const canvas = document.getElementById(canvasElementId);
        const ctx = canvas.getContext('2d');
        canvas.width = this.videoElement.videoWidth;
        canvas.height = this.videoElement.videoHeight;
        ctx.drawImage(this.videoElement, 0, 0, canvas.width, canvas.height);
        return canvas;
    },

    /**
     * Mengambil frame sebagai base64 string (dipakai untuk presensi real time
     * karena dikirim sebagai JSON, bukan FormData).
     */
    captureFrameBase64(canvasElementId) {
        const canvas = this.captureFrame(canvasElementId);
        return canvas.toDataURL('image/jpeg', 0.85);
    },

    /**
     * Mengambil frame sebagai Blob (dipakai saat registrasi, dikirim sebagai file).
     */
    captureFrameBlob(canvasElementId) {
        return new Promise((resolve) => {
            const canvas = this.captureFrame(canvasElementId);
            canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.9);
        });
    },

    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }
};
