from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from db import get_connection

import json
import os

app = Flask(__name__)
CORS(app)

@app.route("/api/tulokset")
def hae_tulokset():
    yhteys = get_connection()
    cursor = yhteys.cursor(dictionary=True)
    cursor.execute("SELECT * FROM results")
    tulokset = cursor.fetchall()
    cursor.close()
    yhteys.close()
    return jsonify(tulokset)

# LÄHETÄ Kartan tietoja front endin#
@app.route("/api/location")
def hae_sijainti():
    if not os.path.exists("location.json"): 
        return jsonify({"error": "Location data not found"}), 404
    
    try:
        with open("location.json", "r") as f:
            data = json.load(f)
        return jsonify(data)   
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/")
def home():
    return send_from_directory('.', 'tulokset.html')

if __name__ == "__main__":
    app.run(debug=True)
