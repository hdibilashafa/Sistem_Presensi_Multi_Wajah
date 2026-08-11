/**
 * realtime_clock.js - Menampilkan tanggal & jam real-time di pojok kanan
 * atas halaman, di-update setiap detik. Dipakai di base_admin.html dan
 * base_user.html.
 */

document.addEventListener('DOMContentLoaded', () => {
    const clockEl = document.getElementById('realtime-clock');
    if (!clockEl) return;

    const hariList = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', "Jumat", 'Sabtu'];
    const bulanList = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ];

    function updateClock() {
        const now = new Date();
        const hari = hariList[now.getDay()];
        const tanggal = now.getDate();
        const bulan = bulanList[now.getMonth()];
        const tahun = now.getFullYear();

        const jam = String(now.getHours()).padStart(2, '0');
        const menit = String(now.getMinutes()).padStart(2, '0');
        const detik = String(now.getSeconds()).padStart(2, '0');

        clockEl.innerHTML = `
            <span class="clock-date">${hari}, ${tanggal} ${bulan} ${tahun}</span>
            <span class="clock-time">${jam}:${menit}:${detik}</span>
        `;
    }

    updateClock();
    setInterval(updateClock, 1000);
});
