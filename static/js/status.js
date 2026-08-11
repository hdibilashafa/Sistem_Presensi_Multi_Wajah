/**
 * status.js - Logika halaman Status Kehadiran (user):
 * cari user (nama/ID) lewat search box -> pilih dari hasil pencarian ->
 * filter rentang tanggal -> tampilkan riwayat -> ekspor csv.
 *
 * Pencarian dilakukan di sisi client terhadap window.ALL_USERS yang
 * dikirim dari server (daftar user tidak besar untuk sistem presensi
 * skala ini, sehingga tidak perlu request ke server tiap ketikan).
 */

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-user-input');
    const searchResults = document.getElementById('search-results');
    const selectedUserBadge = document.getElementById('selected-user-badge');
    const selectedUserText = document.getElementById('selected-user-text');
    const btnClearUser = document.getElementById('btn-clear-user');

    const filterStart = document.getElementById('filter-start');
    const filterEnd = document.getElementById('filter-end');
    const btnFilter = document.getElementById('btn-filter');
    const btnExport = document.getElementById('btn-export');
    const riwayatTableBody = document.getElementById('riwayat-table-body');
    const statusSummary = document.getElementById('status-summary');
    const totalKehadiranEl = document.getElementById('total-kehadiran');

    let selectedUserId = null;
    const allUsers = window.ALL_USERS || [];

    // ===== Pencarian user =====
    searchInput.addEventListener('input', () => {
        const keyword = searchInput.value.trim().toLowerCase();
        if (!keyword) {
            searchResults.style.display = 'none';
            return;
        }

        const matched = allUsers.filter(u =>
            u.nama.toLowerCase().includes(keyword) || String(u.id).includes(keyword)
        );

        renderSearchResults(matched);
    });

    function renderSearchResults(users) {
        if (users.length === 0) {
            searchResults.innerHTML = '<div class="search-result-item text-muted">Tidak ditemukan.</div>';
            searchResults.style.display = 'block';
            return;
        }

        searchResults.innerHTML = users.map(u => `
            <div class="search-result-item" data-id="${u.id}" data-nama="${u.nama}">
                ${u.nama} <span class="search-result-id">(ID: ${u.id})</span>
            </div>
        `).join('');
        searchResults.style.display = 'block';

        searchResults.querySelectorAll('.search-result-item[data-id]').forEach(item => {
            item.addEventListener('click', () => {
                selectUser(item.dataset.id, item.dataset.nama);
            });
        });
    }

    function selectUser(id, nama) {
        selectedUserId = id;
        selectedUserText.textContent = `${nama} (ID: ${id})`;
        selectedUserBadge.style.display = 'block';
        searchInput.value = '';
        searchInput.style.display = 'none';
        searchResults.style.display = 'none';
    }

    btnClearUser.addEventListener('click', () => {
        selectedUserId = null;
        selectedUserBadge.style.display = 'none';
        searchInput.style.display = 'block';
        searchInput.value = '';
        riwayatTableBody.innerHTML = '<tr><td colspan="2" class="text-muted">Cari dan pilih user terlebih dahulu.</td></tr>';
        statusSummary.style.display = 'none';
    });

    // Tutup dropdown hasil pencarian jika klik di luar area
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.form-group')) {
            searchResults.style.display = 'none';
        }
    });

    // ===== Filter & tampilkan riwayat =====
    btnFilter.addEventListener('click', loadStatus);

    async function loadStatus() {
        if (!selectedUserId) {
            showToast('Cari dan pilih user terlebih dahulu.', 'error');
            return;
        }

        let url = `/status/${selectedUserId}`;
        const params = new URLSearchParams();
        if (filterStart.value) params.append('start_date', filterStart.value);
        if (filterEnd.value) params.append('end_date', filterEnd.value);
        if (params.toString()) url += `?${params.toString()}`;

        const res = await fetch(url);
        const data = await res.json();

        if (!data.success) {
            showToast(data.message, 'error');
            return;
        }

        statusSummary.style.display = 'grid';
        totalKehadiranEl.textContent = data.total_kehadiran;

        if (data.riwayat.length === 0) {
            riwayatTableBody.innerHTML = '<tr><td colspan="2" class="text-muted">Belum ada riwayat kehadiran pada rentang ini.</td></tr>';
            return;
        }

        riwayatTableBody.innerHTML = data.riwayat.map(r => `
            <tr>
                <td>${r.tanggal}</td>
                <td class="text-mono">${r.similarity_score.toFixed(4)}</td>
            </tr>
        `).join('');
    }

    // ===== Ekspor csv =====
    btnExport.addEventListener('click', () => {
        if (!selectedUserId) {
            showToast('Cari dan pilih user terlebih dahulu.', 'error');
            return;
        }

        let url = `/status/${selectedUserId}/export`;
        const params = new URLSearchParams();
        if (filterStart.value) params.append('start_date', filterStart.value);
        if (filterEnd.value) params.append('end_date', filterEnd.value);
        if (params.toString()) url += `?${params.toString()}`;

        window.location.href = url;
    });
});
