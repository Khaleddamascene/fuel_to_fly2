from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask import request
from db import get_connection
import json
import os
import random
import subprocess
import sys
import time
import paaohjelma

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)

# Absolute path to the location.json used by the game
LOCATION_FILE = os.path.join(os.path.dirname(__file__), 'location.json')


@app.route("/api/pelaaja", methods=["POST"])
def luo_pelaaja():
    try:
        data = request.get_json()
        player_name = data.get("player_name", "").strip()

        if not player_name:
            return jsonify({"error": "Pelaajan nimi puuttuu"}), 400

        yhteys = get_connection()
        cursor = yhteys.cursor()

        cursor.execute(
            "INSERT INTO results (player_name) VALUES (%s)",
            (player_name,)
        )
        yhteys.commit()
        cursor.close()
        yhteys.close()

        return jsonify({"message": "Pelaaja lisätty onnistuneesti"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



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
    if not os.path.exists(LOCATION_FILE):
        return jsonify({"error": "Location data not found"}), 404

    try:
        with open(LOCATION_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ______________________________hae_sijainti loppuu



# --- PELI VALINNAT --- #
@app.route("/api/peli_valinnat", methods=["POST"])
def peli_valinnat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON-data puuttuu"}), 400

        current_lat = data.get("lat")
        current_lon = data.get("lon")
        kayty_kentat = data.get("kayty_kentat", [])

        if current_lat is None or current_lon is None:
            return jsonify({"error": "current_lat ja current_lon vaaditaan"}), 400

        options = paaohjelma.get_peli_valinnat(current_lat, current_lon, kayty_kentat)
        return jsonify({"choices": options})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Optional GET support for testing --- #
@app.route("/api/peli_valinnat", methods=["GET"])
def peli_valinnat_get():
    return jsonify({"message": "POST JSON-data lat, lon, kayty_kentat"}) 

# _______________________________ def get_Valinnat loppu_____________________


# Endpoint to start the game subprocess (e.g. `paaohjelma.py`)
@app.route("/api/start_game", methods=["POST"])
def start_game():
    """
    Starts `paaohjelma.py` as a background process if it is not already running.

    Security: if environment variable START_TOKEN is set, the POST body must
    include JSON {"token": "..."} matching it. If START_TOKEN is not set,
    the endpoint allows the request (use with care).
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        required_token = os.environ.get("START_TOKEN")
        if required_token:
            if not data.get("token") or data.get("token") != required_token:
                return jsonify({"error": "Invalid or missing token"}), 403

        # Keep track of started processes in module-global dict
        if not hasattr(app, "started_processes"):
            app.started_processes = {}

        # If already started and process is alive, return OK
        proc = app.started_processes.get("paaohjelma")
        if proc and proc.poll() is None:
            return jsonify({"status": "already_running", "pid": proc.pid})

        # Build command to run paaohjelma.py (same Python interpreter)
        script_path = os.path.join(os.path.dirname(__file__), "paaohjelma.py")
        if not os.path.exists(script_path):
            return jsonify({"error": "paaohjelma.py not found"}), 500

        # Start the process with stdin pipe so we can send simulated 'Enter' presses
        popen = subprocess.Popen(
            [sys.executable, script_path],
            cwd=os.path.dirname(__file__),
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        app.started_processes["paaohjelma"] = popen

        # Give the process a short moment to start and begin reading stdin
        try:
            time.sleep(0.2)
            if popen.stdin:
                # send two Enters so the program can advance (as requested)
                popen.stdin.write(b"\n\n")
                popen.stdin.flush()
        except Exception:
            # If we can't write to stdin, still consider process started
            pass

        return jsonify({"status": "started", "pid": popen.pid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/send_name', methods=['POST'])
def send_name():
    """Send player's name to the running paaohjelma process stdin.

    Body JSON: {"player_name": "Name", "start_if_missing": true/false}
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        player_name = (data.get('player_name') or '').strip()
        if not player_name:
            return jsonify({'error': 'player_name required'}), 400

        start_if_missing = bool(data.get('start_if_missing', True))

        # Ensure started_processes exists
        if not hasattr(app, 'started_processes'):
            app.started_processes = {}

        proc = app.started_processes.get('paaohjelma')
        # If process missing or not running, optionally start it
        if (not proc or proc.poll() is not None):
            if not start_if_missing:
                return jsonify({'error': 'paaohjelma not running'}), 409

            # reuse start logic: start process and send initial Enters
            script_path = os.path.join(os.path.dirname(__file__), 'paaohjelma.py')
            if not os.path.exists(script_path):
                return jsonify({'error': 'paaohjelma.py not found'}), 500

            proc = subprocess.Popen([
                sys.executable, script_path
            ], cwd=os.path.dirname(__file__), stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            app.started_processes['paaohjelma'] = proc
            try:
                time.sleep(0.2)
                if proc.stdin:
                    proc.stdin.write(b"\n\n")
                    proc.stdin.flush()
            except Exception:
                pass

        # Now send the player's name followed by newline
        if proc and proc.poll() is None and proc.stdin:
            try:
                tosend = (player_name + '\n').encode('utf-8')
                proc.stdin.write(tosend)
                proc.stdin.flush()
                return jsonify({'status': 'sent'})
            except Exception as e:
                return jsonify({'error': f'failed to write stdin: {e}'}), 500
        else:
            return jsonify({'error': 'paaohjelma not running or no stdin'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/")
def home():
    return send_from_directory('.', 'tulokset.html')

if __name__ == "__main__":
    app.run(debug=True)

