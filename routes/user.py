
import csv
import io
from flask import Blueprint, request, jsonify, render_template, Response
from database.models import UserModel, PresensiModel

user_bp = Blueprint('user', __name__)


@user_bp.route('/status')
def status_page():
    users_raw = UserModel.get_all()
    users = [{'id': u['id'], 'nama': u['nama']} for u in users_raw]
    return render_template('user/status.html', users=users)


@user_bp.route('/status/<string:user_id>')
def get_status(user_id):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    user = UserModel.get_by_id(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User tidak ditemukan.'}), 404

    if start_date and end_date:
        riwayat = PresensiModel.get_by_user(user_id, start_date, end_date)
    else:
        riwayat = PresensiModel.get_by_user(user_id)

    return jsonify({
        'success': True,
        'user': {'id': user['id'], 'nama': user['nama']},
        'total_kehadiran': len(riwayat),
        'riwayat': [
            {
                'tanggal': str(r['waktuPresensi']),
                'similarity_score': r['scoreSimilarity']
            } for r in riwayat
        ]
    })


@user_bp.route('/status/<string:user_id>/export')
def export_user_report(user_id):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    user = UserModel.get_by_id(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User tidak ditemukan.'}), 404

    if start_date and end_date:
        riwayat = PresensiModel.get_by_user(user_id, start_date, end_date)
    else:
        riwayat = PresensiModel.get_by_user(user_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nama', 'Similarity Score', 'Waktu'])

    for r in riwayat:
        writer.writerow([r['nama'], r['scoreSimilarity'], r['waktuPresensi']])

    output.seek(0)
    filename = f"presensi_{user['nama'].replace(' ', '_')}.csv"

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )
