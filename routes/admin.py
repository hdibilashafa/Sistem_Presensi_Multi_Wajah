
import csv
import io
from flask import Blueprint, request, jsonify, render_template, Response
from database.models import UserModel, EmbeddingModel, PresensiModel
from core.embedding_cache import embedding_cache

admin_bp = Blueprint('admin', __name__)


                                         

@admin_bp.route('/admin/dashboard')
def dashboard():
    total_user = len(UserModel.get_all())
    hadir_hari_ini = PresensiModel.get_today_count()
    daftar_hadir = PresensiModel.get_today_list()
    total_presensi = PresensiModel.get_total_count()

    return render_template(
        'admin/dashboard.html',
        total_user=total_user,
        hadir_hari_ini=hadir_hari_ini,
        daftar_hadir=daftar_hadir,
        total_presensi=total_presensi
    )


                                                     

@admin_bp.route('/admin/users')
def users_page():
    users_raw = UserModel.get_all()
    users = [
        {
            'id': u['id'],
            'nama': u['nama'],
            'punya_embedding': UserModel.has_embedding(u['id'])
        }
        for u in users_raw
    ]
    return render_template('admin/users.html', users=users)


@admin_bp.route('/admin/users/search', methods=['GET'])
def search_users():
    keyword = request.args.get('q', '').strip()
    if keyword:
        users = UserModel.search(keyword)
    else:
        users = UserModel.get_all()

    result = [{'id': u['id'], 'nama': u['nama'],
               'punya_embedding': UserModel.has_embedding(u['id'])} for u in users]
    return jsonify({'success': True, 'users': result})


@admin_bp.route('/admin/users/<string:user_id>/update', methods=['POST'])
def update_user(user_id):
    nama = request.form.get('nama', '').strip()
    if not nama:
        return jsonify({'success': False, 'message': 'Nama tidak boleh kosong.'}), 400

    UserModel.update(user_id, nama)
    embedding_cache.refresh()                              
    return jsonify({'success': True, 'message': 'Data user berhasil diperbarui.'})


@admin_bp.route('/admin/users/<string:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    UserModel.delete(user_id)
    embedding_cache.refresh()                                              
    return jsonify({'success': True, 'message': 'Data user berhasil dihapus.'})


                                                

@admin_bp.route('/admin/report')
def report_page():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if start_date and end_date:
        data = PresensiModel.get_all(start_date, end_date)
    else:
        data = PresensiModel.get_all()

    return render_template(
        'admin/report.html',
        data=data,
        start_date=start_date or '',
        end_date=end_date or ''
    )


@admin_bp.route('/admin/report/export')
def export_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if start_date and end_date:
        data = PresensiModel.get_all(start_date, end_date)
    else:
        data = PresensiModel.get_all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID Presensi', 'User ID', 'Nama', 'Similarity Score', 'Waktu'])

    for row in data:
        writer.writerow([
            row['id'], row['user_id'], row['nama'],
            row['scoreSimilarity'], row['waktuPresensi']
        ])

    output.seek(0)
    filename = 'laporan_presensi.csv'
    if start_date and end_date:
        filename = f'laporan_presensi_{start_date}_sd_{end_date}.csv'

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )
