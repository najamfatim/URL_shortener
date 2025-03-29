from flask import Flask, request, jsonify, redirect
from flask_cors import CORS  # Import CORS
import mysql.connector
import random
import string

app = Flask(__name__)
CORS(app) 

# Store shortened URLs in a dictionary (for now)
url_mapping = {}

@app.route('/')
def home():
    return "Flask App is Running!"

# MySQL Database Configuration
db_config = {
    "host": "localhost",
    "user": "root",  # Change if needed
    "password": "root",  # Enter your MySQL password
    "database": "url_shortener"
}

# Function to generate a short code
def generate_short_code(length=6):
    """Generates a random short code for the URL"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# **1. Create a short URL**
@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    """Shortens a given URL"""
    data = request.json
    original_url = data.get("url")

    if not original_url:
        return jsonify({"error": "No URL provided"}), 400

    short_code = generate_short_code()
    url_mapping[short_code] = original_url

    short_url = f"http://127.0.0.1:5000/{short_code}"
    return jsonify({"short_url": short_url})

# **2. Retrieve the original URL**
@app.route('/api/url/<short_code>', methods=['GET'])
def get_original_url(short_code):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT original_url, access_count FROM urls WHERE short_code = %s", (short_code,))
    result = cursor.fetchone()

    if not result:
        return jsonify({"error": "Short URL not found"}), 404

    original_url, access_count = result

    # Update access count
    cursor.execute("UPDATE urls SET access_count = access_count + 1 WHERE short_code = %s", (short_code,))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"original_url": original_url, "short_code": short_code, "access_count": access_count + 1}), 200

@app.route('/<short_code>', methods=['GET'])
def redirect_to_original(short_code):
    """Redirects to the original URL"""
    original_url = url_mapping.get(short_code)

    if original_url:
        return jsonify({"redirect_to": original_url})
    else:
        return jsonify({"error": "Invalid short URL"}), 404
    
# **3. Update the Short URL**
@app.route('/api/url/<short_code>', methods=['PUT'])
def update_short_url(short_code):
    data = request.get_json()
    if 'url' not in data:
        return jsonify({"error": "URL is required"}), 400

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("UPDATE urls SET original_url = %s, updated_at = NOW() WHERE short_code = %s", (data['url'], short_code))
    conn.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Short URL not found"}), 404

    cursor.close()
    conn.close()

    return jsonify({"message": "URL updated successfully", "short_code": short_code}), 200

# **4. Delete the Short URL**
@app.route('/api/url/<short_code>', methods=['DELETE'])
def delete_short_url(short_code):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM urls WHERE short_code = %s", (short_code,))
    conn.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Short URL not found"}), 404

    cursor.close()
    conn.close()

    return '', 204  # No Content response

# **5. Get URL Statistics**
@app.route('/api/url/<short_code>/stats', methods=['GET'])
def get_url_stats(short_code):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT id, original_url, short_code, created_at, updated_at, access_count FROM urls WHERE short_code = %s", (short_code,))
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if not result:
        return jsonify({"error": "Short URL not found"}), 404

    return jsonify({
        "id": result[0],
        "original_url": result[1],
        "short_code": result[2],
        "created_at": result[3],
        "updated_at": result[4],
        "access_count": result[5]
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
