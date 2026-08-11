import json
import numpy as np
from flask_mysqldb import MySQL

mysql = MySQL()


class UserModel:

    @staticmethod
    def get_all():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user ORDER BY waktuRegistrasi DESC")
        users = cur.fetchall()
        cur.close()
        return users

    @staticmethod
    def get_by_id(user_id):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        return user

    @staticmethod
    def search(keyword):
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT * FROM user WHERE nama LIKE %s OR id LIKE %s ORDER BY waktuRegistrasi DESC",
            (f'%{keyword}%', f'%{keyword}%')
        )
        users = cur.fetchall()
        cur.close()
        return users

    @staticmethod
    def create(user_id, nama):
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user (id, nama) VALUES (%s, %s)", (user_id, nama))
        mysql.connection.commit()
        cur.close()
        return user_id

    @staticmethod
    def exists(user_id):
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM user WHERE id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        return result is not None

    @staticmethod
    def update(user_id, nama):
        cur = mysql.connection.cursor()
        cur.execute("UPDATE user SET nama = %s WHERE id = %s", (nama, user_id))
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def delete(user_id):
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM user WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def has_embedding(user_id):
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM fiturWajah WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        return result is not None


class EmbeddingModel:

    @staticmethod
    def save(user_id, embedding_vector):
        embedding_json = json.dumps(embedding_vector.tolist())
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM fiturWajah WHERE user_id = %s", (user_id,))
        cur.execute(
            "INSERT INTO fiturWajah (user_id, fiturWajah) VALUES (%s, %s)",
            (user_id, embedding_json)
        )
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def get_all():
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT f.user_id, f.fiturWajah, u.nama
            FROM fiturWajah f
            JOIN user u ON f.user_id = u.id
        """)
        rows = cur.fetchall()
        cur.close()

        embeddings = {}
        for row in rows:
            embeddings[row['user_id']] = {
                'nama': row['nama'],
                'embedding': np.array(json.loads(row['fiturWajah']))
            }
        return embeddings

    @staticmethod
    def delete(user_id):
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM fiturWajah WHERE user_id = %s", (user_id,))
        mysql.connection.commit()
        cur.close()


class PresensiModel:

    @staticmethod
    def already_presensi_today(user_id):
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id FROM presensi
            WHERE user_id = %s AND DATE(waktuPresensi) = CURDATE()
            LIMIT 1
        """, (user_id,))
        result = cur.fetchone()
        cur.close()
        return result is not None

    @staticmethod
    def save(user_id, similarity_score):
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO presensi (user_id, scoreSimilarity) VALUES (%s, %s)",
            (user_id, similarity_score)
        )
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def get_all(start_date=None, end_date=None):
        cur = mysql.connection.cursor()
        query = """
            SELECT p.id, u.nama, u.id AS user_id, p.scoreSimilarity, p.waktuPresensi
            FROM presensi p
            JOIN user u ON p.user_id = u.id
        """
        params = []
        if start_date and end_date:
            query += " WHERE DATE(p.waktuPresensi) BETWEEN %s AND %s"
            params = [start_date, end_date]
        query += " ORDER BY p.waktuPresensi DESC"
        cur.execute(query, params)
        result = cur.fetchall()
        cur.close()
        return result

    @staticmethod
    def get_by_user(user_id, start_date=None, end_date=None):
        cur = mysql.connection.cursor()
        query = """
            SELECT p.id, u.nama, p.scoreSimilarity, p.waktuPresensi
            FROM presensi p
            JOIN user u ON p.user_id = u.id
            WHERE p.user_id = %s
        """
        params = [user_id]
        if start_date and end_date:
            query += " AND DATE(p.waktuPresensi) BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        query += " ORDER BY p.waktuPresensi DESC"
        cur.execute(query, params)
        result = cur.fetchall()
        cur.close()
        return result

    @staticmethod
    def get_today_count():
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT COUNT(DISTINCT user_id) AS count
            FROM presensi
            WHERE DATE(waktuPresensi) = CURDATE()
        """)
        result = cur.fetchone()
        cur.close()
        return result['count'] if result else 0

    @staticmethod
    def get_today_list():
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT u.id AS user_id, u.nama, MAX(p.waktuPresensi) AS waktu_terakhir
            FROM presensi p
            JOIN user u ON p.user_id = u.id
            WHERE DATE(p.waktuPresensi) = CURDATE()
            GROUP BY p.user_id, u.nama
            ORDER BY waktu_terakhir DESC
        """)
        result = cur.fetchall()
        cur.close()
        return result

    @staticmethod
    def get_total_count():
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) AS count FROM presensi")
        result = cur.fetchone()
        cur.close()
        return result['count'] if result else 0


class ConfigModel:

    @staticmethod
    def get_threshold():
        cur = mysql.connection.cursor()
        cur.execute("SELECT configValue FROM sistemConfig WHERE configKey = 'threshold'")
        result = cur.fetchone()
        cur.close()
        return float(result['configValue']) if result else 0.5

    @staticmethod
    def set_threshold(value):
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO sistemConfig (configKey, configValue) VALUES ('threshold', %s)
            ON DUPLICATE KEY UPDATE configValue = %s
        """, (value, value))
        mysql.connection.commit()
        cur.close()
