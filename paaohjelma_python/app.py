from flask import Flask, jsonify, request, send_from_directory, session 
from flask_cors import CORS
from db import get_connection
import json
import os
import random

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)

# NÄYTÄ Tulokset front endin#
@app.route("/api/tulokset")
def hae_tulokset():
    yhteys = get_connection()
    cursor = yhteys.cursor(dictionary=True)
    cursor.execute("SELECT * FROM results")
    tulokset = cursor.fetchall()
    cursor.close()
    yhteys.close()
    return jsonify(tulokset)

@app.route("/api/pelaaja/<int:pelaaja_id>")
def pelaaja_data(pelaaja_id):
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
    
# ______________________________hae_sijainti loppuu 


# _______________________________Tässä haetaan tietokanasta 3 lentokenttä jä tehdään route _____________________
@app.route("/api/get_Valinnat", methods=["GET"])
def get_Valinnat():
    try:
        yhteys = get_connection()
        cursor = yhteys.cursor(dictionary=True)
        
        # Valitaan satunnaisesti 3 lentokenttää tietokannasta
        cursor.execute("""
            SELECT a.ident, a.name, a.latitude_deg, a.longitude_deg, 
                   a.municipality, c.name AS country_name
            FROM airport a
            LEFT JOIN country c ON a.iso_country = c.iso_country
            WHERE a.latitude_deg IS NOT NULL
              AND a.longitude_deg IS NOT NULL
            ORDER BY RAND()
            LIMIT 3
        """)
        
        airports = cursor.fetchall()
        cursor.close()
        yhteys.close()
        
        response_choices = []
        for airport in airports:
            airport_info = airport.copy()
            airport_info["distance"] = round(random.uniform(100, 5000), 2)  
            response_choices.append(airport_info)
        
        return jsonify({
            "choices": response_choices,
            "current_fuel": 1000,
            "message": "Valitse seuraava lentokenttä:"
        })
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500
# _______________________________ def get_Valinnat loppu_____________________

@app.route("/")
def home():
    return send_from_directory('.', 'tulokset.html')

if __name__ == "__main__":
    app.run(debug=True)
