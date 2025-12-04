from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from db import get_connection

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

@app.route("/")
def home():
    return send_from_directory('.', 'tulokset.html')

if __name__ == "__main__":
    app.run(debug=True)
