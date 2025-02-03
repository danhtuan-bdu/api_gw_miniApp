from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
import mysql.connector
import os

# Initialize the Flask app
app = Flask(__name__)
auth = HTTPBasicAuth()

# Configuration parameters
DEFAULT_USERNAME = os.getenv('BASIC_AUTH_USERNAME', 'ioc_bdu_api')
DEFAULT_PASSWORD = os.getenv('BASIC_AUTH_PASSWORD', '*Bdu@apigw2024')

DEFAULT_DB_CONFIG = {
    'host': os.getenv('DB_HOST', '192.168.69.26'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '*Bdu@mysqlapi2024'),
    'database': os.getenv('DB_NAME', 'IOC_BDU_ODP')
}

DB_CONFIG = {
    'host': DEFAULT_DB_CONFIG['host'],
    'user': DEFAULT_DB_CONFIG['user'],
    'password': DEFAULT_DB_CONFIG['password'],
    'database': DEFAULT_DB_CONFIG['database'],
    'auth_plugin': 'mysql_native_password'
}

# Verify password function to check against API credentials
@auth.verify_password
def verify_password(username, password):
    return username == DEFAULT_USERNAME and password == DEFAULT_PASSWORD

# Function to fetch data from MySQL database with parameters
def get_data_from_db(table_name, mssv, created_at, ngay_origin):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        query = f"SELECT * FROM `{table_name}`"  # Securely wrap table name
        params = []
        conditions = []

        if mssv:
            conditions.append("mssv = %s")
            params.append(mssv)

        if created_at:
            conditions.append("created_at = %s")
            params.append(created_at)

        if ngay_origin:
            conditions.append("ngay_origin = %s")
            params.append(ngay_origin)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()
        return rows

    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        return {"error": f"Database error: {str(err)}"}

# Route to fetch data with input parameters
@app.route('/data/<table_name>', methods=['GET'])
@auth.login_required
def get_data(table_name):
    valid_tables = [
        'dim_bang_diem_odp', 'dim_chuyen_nganh_odp', 'dim_danh_sach_diem_danh_odp',
        'dim_giang_vien_odp', 'dim_he_dao_tao_odp', 'dim_khoa_odp', 'dim_lop_odp',
        'dim_mon_dang_ky_odp', 'dim_mon_hoc_odp', 'diem_nganh_odp',
        'fact_ho_so_sinh_vien_odp', 'fact_nhom_hoc_odp'
    ]

    if table_name not in valid_tables:
        return jsonify({"error": "Invalid table name"}), 400

    # Get input parameters from the request
    mssv = request.args.get('mssv')
    created_at = request.args.get('created_at')
    ngay_origin = request.args.get('ngay_origin')

    # Fetch data from the database
    data = get_data_from_db(table_name, mssv, created_at, ngay_origin)

    if isinstance(data, dict) and "error" in data:
        return jsonify(data), 500

    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
