/**
 * users.js - Logika halaman Data User: pencarian, edit inline, hapus.
 */

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const tableBody = document.getElementById('user-table-body');

    // ===== Pencarian user (debounced) =====
    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => searchUsers(searchInput.value), 300);
    });

    async function searchUsers(keyword) {
        const res = await fetch(`/admin/users/search?q=${encodeURIComponent(keyword)}`);
        const data = await res.json();

        if (!data.success) return;

        tableBody.innerHTML = '';
        if (data.users.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="4" class="text-muted">Tidak ada user yang cocok.</td></tr>`;
            return;
        }

        data.users.forEach(u => {
            const row = document.createElement('tr');
            row.dataset.userId = u.id;
            row.innerHTML = `
                <td class="text-mono">${u.id}</td>
                <td>
                    <span class="view-mode">${u.nama}</span>
                    <input type="text" class="form-input edit-mode" style="display:none;" value="${u.nama}">
                </td>
                <td>${u.punya_embedding ? '<span class="badge badge-success">Terdaftar</span>' : '<span class="badge badge-neutral">Belum ada wajah</span>'}</td>
                <td class="flex gap-8">
                    <button class="btn btn-secondary btn-edit">Ubah</button>
                    <button class="btn btn-secondary btn-save" style="display:none;">Simpan</button>
                    <button class="btn btn-danger btn-delete">Hapus</button>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }

    // ===== Edit, Simpan, Hapus (event delegation) =====
    tableBody.addEventListener('click', async (e) => {
        const row = e.target.closest('tr');
        if (!row || !row.dataset.userId) return;
        const userId = row.dataset.userId;

        // --- Tombol Ubah ---
        if (e.target.classList.contains('btn-edit')) {
            row.querySelector('.view-mode').style.display = 'none';
            row.querySelector('.edit-mode').style.display = 'block';
            row.querySelector('.btn-edit').style.display = 'none';
            row.querySelector('.btn-save').style.display = 'inline-flex';
        }

        // --- Tombol Simpan ---
        if (e.target.classList.contains('btn-save')) {
            const newName = row.querySelector('.edit-mode').value.trim();
            if (!newName) {
                showToast('Nama tidak boleh kosong.', 'error');
                return;
            }

            const formData = new FormData();
            formData.append('nama', newName);

            const res = await fetch(`/admin/users/${userId}/update`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.success) {
                row.querySelector('.view-mode').textContent = newName;
                row.querySelector('.view-mode').style.display = 'inline';
                row.querySelector('.edit-mode').style.display = 'none';
                row.querySelector('.btn-edit').style.display = 'inline-flex';
                row.querySelector('.btn-save').style.display = 'none';
                showToast('Data user berhasil diperbarui.');
            } else {
                showToast(data.message, 'error');
            }
        }

        // --- Tombol Hapus ---
        if (e.target.classList.contains('btn-delete')) {
            const nama = row.querySelector('.view-mode').textContent;
            if (!confirm(`Hapus user "${nama}"? Seluruh data wajah dan riwayat presensinya akan ikut terhapus.`)) {
                return;
            }

            const res = await fetch(`/admin/users/${userId}/delete`, { method: 'POST' });
            const data = await res.json();

            if (data.success) {
                row.remove();
                showToast('User berhasil dihapus.');
            } else {
                showToast(data.message, 'error');
            }
        }
    });
});
