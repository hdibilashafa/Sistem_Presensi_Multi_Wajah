/**
 * evaluation.js - Logika halaman Evaluasi ROC:
 * ambil data genuine/impostor lewat kamera -> tampil LANGSUNG di daftar
 * (tanpa reload halaman) -> jalankan analisis -> tampilkan tabel TPR/FPR,
 * grafik ROC, dan rekomendasi threshold optimal.
 */

document.addEventListener('DOMContentLoaded', () => {
    const btnRunAnalysis = document.getElementById('btn-run-analysis');
    const btnResetScores = document.getElementById('btn-reset-scores');
    const rocResult = document.getElementById('roc-result');
    const currentThresholdDisplay = document.getElementById('current-threshold-display');

    const listGenuineEl = document.getElementById('list-genuine');
    const listImpostorEl = document.getElementById('list-impostor');
    const countGenuineEl = document.getElementById('count-genuine');
    const countImpostorEl = document.getElementById('count-impostor');
    const totalGenuineDisplay = document.getElementById('total-genuine-display');
    const totalImpostorDisplay = document.getElementById('total-impostor-display');

    // Data awal dikirim langsung dari server saat halaman dimuat
    // (lihat templates/admin/evaluation.html), supaya tidak perlu
    // fetch tambahan hanya untuk menampilkan apa yang sudah ada.
    renderScoreLists(window.INITIAL_GENUINE_SCORES || [], window.INITIAL_IMPOSTOR_SCORES || []);

    // ===== Ambil Data via Kamera (Otomatis) =====
    const selectTrueIdentity = document.getElementById('select-true-identity');
    const btnEvalCameraStart = document.getElementById('btn-eval-camera-start');
    const btnEvalCapture = document.getElementById('btn-eval-capture');
    const evalCaptureResult = document.getElementById('eval-capture-result');

    let evalCameraActive = false;

    btnEvalCameraStart.addEventListener('click', async () => {
        const ready = await CameraModule.start('eval-camera-feed');
        if (!ready) return;

        evalCameraActive = true;
        btnEvalCameraStart.disabled = true;
        btnEvalCapture.disabled = false;
        showToast('Kamera aktif. Posisikan wajah, lalu klik "Ambil & Proses".');
    });

    btnEvalCapture.addEventListener('click', async () => {
        if (!evalCameraActive) return;

        btnEvalCapture.disabled = true;
        btnEvalCapture.textContent = 'Memproses...';

        try {
            const imageBase64 = CameraModule.captureFrameBase64('eval-capture-canvas');
            const trueUserId = selectTrueIdentity.value || null;

            const res = await fetch('/admin/evaluation/capture', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: imageBase64, true_user_id: trueUserId })
            });
            const data = await res.json();

            if (!data.success) {
                showToast(data.message || 'Gagal memproses wajah.', 'error');
                evalCaptureResult.innerHTML = `<div class="alert alert-error">${data.message}</div>`;
                return;
            }

            renderCaptureBreakdown(data.breakdown);
            renderScoreLists(data.genuine_scores, data.impostor_scores);

            const totalGenuineBaru = data.breakdown.filter(b => b.label === 'genuine').length;
            const totalImpostorBaru = data.breakdown.filter(b => b.label === 'impostor').length;
            showToast(`1 wajah diproses -> ${totalGenuineBaru} skor genuine, ${totalImpostorBaru} skor impostor ditambahkan.`);
        } catch (err) {
            console.error('Gagal memproses capture:', err);
            showToast('Terjadi kesalahan saat memproses frame.', 'error');
        } finally {
            btnEvalCapture.disabled = false;
            btnEvalCapture.textContent = 'Ambil & Proses Wajah Ini';
        }
    });

    /**
     * Menampilkan rincian hasil perbandingan 1x capture terhadap SELURUH
     * embedding referensi, supaya admin bisa lihat persis skor apa yang
     * baru saja masuk sebagai genuine/impostor (bukan cuma jumlah totalnya).
     */
    function renderCaptureBreakdown(breakdown) {
        const rows = breakdown.map(b => `
            <div class="flex-between" style="padding:6px 0; border-bottom:1px solid var(--gray-200); font-size:13px;">
                <span>${b.user_id} &mdash; ${b.nama}</span>
                <span>
                    <span class="text-mono">${b.similarity.toFixed(4)}</span>
                    <span class="badge ${b.label === 'genuine' ? 'badge-success' : 'badge-danger'}" style="margin-left:8px;">
                        ${b.label}
                    </span>
                </span>
            </div>
        `).join('');

        evalCaptureResult.innerHTML = `
            <p class="text-muted" style="font-size:13px; margin-bottom:8px;">
                Hasil perbandingan wajah ini ke seluruh user referensi:
            </p>
            ${rows}
        `;
    }

    btnResetScores.addEventListener('click', async () => {
        if (!confirm('Hapus seluruh data pengujian genuine & impostor?')) return;
        await fetch('/admin/evaluation/reset', { method: 'POST' });
        renderScoreLists([], []);
        evalCaptureResult.innerHTML = '';
        rocResult.innerHTML = '<p class="text-muted">Belum ada hasil analisis.</p>';
        showToast('Seluruh data pengujian telah dihapus.');
    });

    /**
     * Menampilkan daftar skor genuine & impostor sebagai list yang bisa
     * dilihat satu per satu (bukan cuma angka total), masing-masing
     * dengan tombol hapus per-item. Juga meng-update stat card
     * "Data Genuine" / "Data Impostor" di bagian atas halaman supaya
     * angkanya selalu sinkron dengan daftar di bawahnya.
     */
    function renderScoreLists(genuineScores, impostorScores) {
        countGenuineEl.textContent = genuineScores.length;
        countImpostorEl.textContent = impostorScores.length;
        totalGenuineDisplay.textContent = genuineScores.length;
        totalImpostorDisplay.textContent = impostorScores.length;

        listGenuineEl.innerHTML = renderListItems(genuineScores, 'genuine');
        listImpostorEl.innerHTML = renderListItems(impostorScores, 'impostor');

        attachDeleteHandlers();
    }

    function renderListItems(scores, label) {
        if (scores.length === 0) {
            return '<div class="score-list-empty">Belum ada data.</div>';
        }

        return scores.map((score, index) => `
            <div class="score-item">
                <span>#${index + 1} &nbsp; ${score.toFixed(4)}</span>
                <span class="score-item-remove" data-label="${label}" data-index="${index}">Hapus</span>
            </div>
        `).join('');
    }

    function attachDeleteHandlers() {
        document.querySelectorAll('.score-item-remove').forEach(el => {
            el.addEventListener('click', async () => {
                const label = el.dataset.label;
                const index = el.dataset.index;

                const res = await fetch('/admin/evaluation/delete_score', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ label, index })
                });
                const data = await res.json();

                if (data.success) {
                    renderScoreLists(data.genuine_scores, data.impostor_scores);
                }
            });
        });
    }

    // ===== Jalankan Analisis ROC =====
    btnRunAnalysis.addEventListener('click', async () => {
        rocResult.innerHTML = '<p class="text-muted">Menjalankan analisis...</p>';

        const res = await fetch('/admin/evaluation/analyze', { method: 'POST' });
        const data = await res.json();

        if (!data.success) {
            rocResult.innerHTML = `<div class="alert alert-error">${data.message}</div>`;
            return;
        }

        renderRocResult(data);
    });

    function renderRocResult(data) {
        const tableRows = data.roc_table.map(row => `
            <tr>
                <td class="text-mono">${row.threshold}</td>
                <td class="text-mono">${row.tpr}</td>
                <td class="text-mono">${row.fpr}</td>
                <td class="text-mono">${row.tp}</td>
                <td class="text-mono">${row.tn}</td>
                <td class="text-mono">${row.fp}</td>
                <td class="text-mono">${row.fn}</td>
            </tr>
        `).join('');

        rocResult.innerHTML = `
            <div class="card-grid" style="margin-bottom:20px;">
                <div class="stat-card">
                    <p class="stat-label">AUC</p>
                    <p class="stat-value">${data.auc}</p>
                </div>
                <div class="stat-card">
                    <p class="stat-label">Threshold Optimal</p>
                    <p class="stat-value accent-success">${data.optimal_threshold}</p>
                </div>
                <div class="stat-card">
                    <p class="stat-label">Youden's Index</p>
                    <p class="stat-value">${data.youden_index}</p>
                </div>
            </div>

            <img src="${data.plot_url}?t=${Date.now()}" alt="Kurva ROC" style="max-width:480px; border:1px solid var(--gray-200); border-radius:10px; margin-bottom:20px;">

            <div class="flex gap-12 mb-24">
                <button class="btn btn-success" id="btn-apply-threshold">
                    Terapkan Threshold ${data.optimal_threshold} ke Sistem
                </button>
            </div>

            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Threshold</th><th>TPR</th><th>FPR</th>
                            <th>TP</th><th>TN</th><th>FP</th><th>FN</th>
                        </tr>
                    </thead>
                    <tbody>${tableRows}</tbody>
                </table>
            </div>
        `;

        document.getElementById('btn-apply-threshold').addEventListener('click', async () => {
            const res = await fetch('/admin/evaluation/apply_threshold', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ threshold: data.optimal_threshold })
            });
            const result = await res.json();

            if (result.success) {
                currentThresholdDisplay.textContent = data.optimal_threshold;
                showToast(result.message);
            }
        });
    }
});
