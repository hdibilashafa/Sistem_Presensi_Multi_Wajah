
import os
import multiprocessing
import tensorflow as tf

                                                                
                                                                      
                                                                      
                                                         
_cpu_count = multiprocessing.cpu_count()
tf.config.threading.set_intra_op_parallelism_threads(_cpu_count)
tf.config.threading.set_inter_op_parallelism_threads(_cpu_count)

from flask import Flask, render_template, redirect, url_for
from flask_mysqldb import MySQL

from config import Config
from database.models import mysql
from core.embedding_cache import embedding_cache

from routes.admin import admin_bp
from routes.user import user_bp
from routes.registration import registration_bp
from routes.presence import presence_bp
from routes.evaluation import evaluation_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

                                
    mysql.init_app(app)

                                 
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(registration_bp)
    app.register_blueprint(presence_bp)
    app.register_blueprint(evaluation_bp)

    @app.route('/')
    def index():
        return redirect(url_for('user.status_page'))

    @app.errorhandler(404)
    def not_found(e):
        return f"<h2>404 - Halaman tidak ditemukan</h2><p><a href='/'>Kembali ke beranda</a></p>", 404

                                                                     
    with app.app_context():
        try:
            total = embedding_cache.load_from_database()
            print(f"[INFO] Embedding cache dimuat: {total} user.")
        except Exception as e:
            print(f"[WARNING] Gagal memuat embedding cache saat start: {e}")
            print("[WARNING] Pastikan database sudah dibuat dari database/schema.sql")

    return app


app = create_app()

if __name__ == '__main__':
    print(f"[INFO] TensorFlow dikonfigurasi memakai {_cpu_count} core CPU.")
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000, threaded=True)
