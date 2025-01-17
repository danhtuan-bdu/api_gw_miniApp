from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
import mysql.connector
import os

# Initialize the Flask app
app = Flask(__name__)
auth = HTTPBasicAuth()

# Configuration parameters
DEFAULT_USERNAME = 'ioc_bdu_api'
DEFAULT_PASSWORD = '*Bdu@apigw2024'
DEFAULT_DB_CONFIG = {
    'host': '192.168.69.26',
    'user': 'root',
    'password': '*Bdu@mysqlapi2024',
    'database': 'IOC_BDU_ODP'
}

# Load configuration from environment variables
app.config['BASIC_AUTH_USERNAME'] = os.getenv('BASIC_AUTH_USERNAME', DEFAULT_USERNAME)
app.config['BASIC_AUTH_PASSWORD'] = os.getenv('BASIC_AUTH_PASSWORD', DEFAULT_PASSWORD)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', DEFAULT_DB_CONFIG['host']),
    'user': os.getenv('DB_USER', DEFAULT_DB_CONFIG['user']),
    'password': os.getenv('DB_PASSWORD', DEFAULT_DB_CONFIG['password']),
    'database': os.getenv('DB_NAME', DEFAULT_DB_CONFIG['database']),
    'auth_plugin': 'mysql_native_password'
}

# Verify password function to check against API credentials
@auth.verify_password
def verify_password(username, password):
    return username == app.config['BASIC_AUTH_USERNAME'] and password == app.config['BASIC_AUTH_PASSWORD']

# Function to fetch data from MySQL database with parameters
def get_data_from_db(table_name, mssv, created_at):
    try:
        # Establish database connection
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Construct SQL query dynamically based on parameters
        query = f"SELECT * FROM {table_name}"
        params = []
        conditions = []

        if mssv:
            conditions.append("mssv = %s")
            params.append(mssv)

        if created_at:
            conditions.append("created_at = %s")
            params.append(created_at)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Execute the query with parameters
        cursor.execute(query, params)

        # Fetch all rows of the query result
        rows = cursor.fetchall()

        # Close the database connection
        cursor.close()
        conn.close()

        return rows
    except mysql.connector.Error as err:
        # Log the error and return None
        app.logger.error(f"Database error: {err}")
        return None

# Route to fetch data with input parameters
@app.route('/data/<table_name>', methods=['GET'])
@auth.login_required  # Protect this route with authentication
def get_data(table_name):
    # Define a list of valid tables for security
    valid_tables = [
        'dim_bang_diem_odp', 'dim_chuyen_nganh_odp', 'dim_danh_sach_diem_danh_odp',
        'dim_giang_vien_odp', 'dim_he_dao_tao_odp', 'dim_khoa_odp', 'dim_lop_odp',
        'dim_mon_dang_ky_odp', 'dim_mon_hoc_odp', 'diem_nganh_odp',
        'fact_ho_so_sinh_vien_odp', 'fact_nhom_hoc_odp'
    ]

    # Validate table name
    if table_name not in valid_tables:
        return jsonify({"error": "Invalid table name"}), 400
# Get input parameters from the request
    mssv = request.args.get('mssv')
    created_at = request.args.get('created_at')

    # Fetch data from the database
    data = get_data_from_db(table_name, mssv, created_at)

    # Check if data retrieval was successful
    if data is None:
        return jsonify({"error": "Failed to retrieve data from the database"}), 500

    # Return the data as JSON
    return jsonify(data)

if __name__ == '__main__':
    # Run the Flask app on port 5001
    app.run(host='0.0.0.0', port=5050, debug=True)