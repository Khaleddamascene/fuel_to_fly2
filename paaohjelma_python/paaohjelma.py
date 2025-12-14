from db import get_connection
import random
from geopy.distance import geodesic
import json
import Visuals
from dotenv import load_dotenv
load_dotenv()

# ===============================
# JSON APUFUNKTIOT
# ===============================

def paivita_location_json(ident, name, lat, lon, fuel):
    with open("location.json", "w", encoding="utf-8") as f:
        json.dump({
            "ident": ident,
            "name": name,
            "lat": lat,
            "lon": lon,
            "fuel": int(fuel)
        }, f, ensure_ascii=False)

VALINNAT_FILE = "valinnat.json"

def tallenna_valinnat_json(vaihtoehdot, fuel):
    data = {
        "fuel": round(fuel, 0),
        "choices": []
    }

    for ident, name, (_, _), municipality, country, continent in vaihtoehdot:
        data["choices"].append({
            "ident": ident,
            "name": name,
            "municipality": municipality,
            "country": country,
            "continent": continent
        })

    with open(VALINNAT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def peli_loppu(nimi=None, kayty_kentat=None, kokonaismatka=None):
    # Tyhjennetään JSON-tiedostot
    paivita_location_json(0, "peli päättynyt", 0, 0, 0)
    with open(VALINNAT_FILE, "w", encoding="utf-8") as f:
        json.dump({"fuel": 0, "choices": []}, f, ensure_ascii=False)
    
    # Tallennetaan tulokset
    if nimi and kayty_kentat is not None and kokonaismatka is not None:
        yhteys = get_connection()
        cursor = yhteys.cursor()

        # Tarkistetaan, onko pelaaja jo olemassa
        cursor.execute(
            "SELECT id FROM results WHERE player_name = %s",
            (nimi,)
        )
        row = cursor.fetchone()

        if row:
            # Pelaaja löytyy → päivitetään olemassa oleva rivi
            cursor.execute(
                "UPDATE results SET visited_count = %s, total_distance = %s WHERE player_name = %s",
                (len(kayty_kentat), kokonaismatka, nimi)
            )
        else:
            # Pelaajaa ei ole → lisätään uusi rivi
            cursor.execute(
                "INSERT INTO results (player_name, visited_count, total_distance) VALUES (%s, %s, %s)",
                (nimi, len(kayty_kentat), kokonaismatka)
            )

        yhteys.commit()
        cursor.close()
        yhteys.close()

# ===============================
# KOMENNOT
# ===============================

def Ohjeet():
    print("\nOHJEET:")
    print("- Lähin kenttä: turvallinen (+1000 polttoainetta)")
    print("- Keskikenttä: tasapainoinen")
    print("- Kaukaisin kenttä: suuri riski")
    print("Jos polttoaine loppuu → peli päättyy\n")
    input("Paina ENTER jatkaaksesi...")

def HaeKomento(s):
    s = s.lower()
    if s in ["ohje", "ohjeet", "o"]:
        Ohjeet()
        return True
    return False

# ===============================
# PELIN ALKU
# ===============================

def alku():
    yhteys = get_connection()
    cursor = yhteys.cursor()

    cursor.execute("""
        SELECT a.ident,
               a.name,
               a.latitude_deg,
               a.longitude_deg,
               a.municipality,
               c.name AS country_name,
               c.continent
        FROM airport a
        LEFT JOIN country c ON a.iso_country = c.iso_country
        WHERE a.latitude_deg IS NOT NULL
          AND a.longitude_deg IS NOT NULL
    """)
    kaikki_kentat = cursor.fetchall()

    nimi = input("Syötä pelaajan nimi: ").strip()
    while not nimi:
        nimi = input("Nimi ei voi olla tyhjä: ").strip()

    aloitus = random.choice(kaikki_kentat)
    ident, name, lat, lon, municipality, country, continent = aloitus

    bensa = 1000.0

    print(f"\nAloitit kentältä {name} ({ident})")
    print(f"Maa: {country}")
    print(f"Polttoaine: {bensa}\n")

    cursor.close()
    yhteys.close()

    paivita_location_json(ident, name, lat, lon, bensa)

    return nimi, kaikki_kentat, (ident, name, (lat, lon)), bensa

# ===============================
# PELIN PÄÄOSA
# ===============================

def pelaa_peli(pelaaja_kentta, kaikki_kentat, kayty_kentat, bensa):
    ident0, name0, sijainti = pelaaja_kentta

    kentat = []
    for ident, name, lat, lon, municipality, country, continent in kaikki_kentat:
        if ident in kayty_kentat:
            continue

        kulutus = geodesic(sijainti, (lat, lon)).km
        kentat.append(
            (ident, name, (lat, lon), municipality, country, continent, kulutus)
        )

    if len(kentat) < 3:
        print("Ei enää uusia kenttiä. Peli päättyy.")
        return None, 0

    kentat.sort(key=lambda x: x[6])

    lahin = kentat[0]
    keskimmainen = kentat[len(kentat)//2]
    kaukaisin = kentat[-1]

    vaihtoehdot = [lahin, keskimmainen, kaukaisin]
    random.shuffle(vaihtoehdot)

    # JSON (ei etäisyyttä)
    tallenna_valinnat_json(
        [(k[0], k[1], k[2], k[3], k[4], k[5]) for k in vaihtoehdot],
        bensa
    )

    print("\nVALITSE SEURAAVA KENTTÄ:")
    for i, k in enumerate(vaihtoehdot, 1):
        print(f"{i}. {k[1]} ({k[0]})")
        print(f"   Kaupunki: {k[3]}")
        print(f"   Maa: {k[4]}")
        print(f"   Maanosa: {k[5]}\n")

    while True:
        s = input("Valinta (1–3): ")
        if HaeKomento(s):
            continue
        if s in ["1", "2", "3"]:
            valinta = int(s) - 1
            break

    valittu = vaihtoehdot[valinta]
    kulutus = valittu[6]

    if bensa < kulutus:
        print("Polttoaine ei riitä.")
        peli_loppu(nimi, kayty_kentat, kokonaismatka=0)
        return None, 0

    bensa -= kulutus

    if valittu == lahin:
        bensa += 1000
        print("Turvallinen lento! +1000 polttoainetta")

    print(f"Polttoainetta jäljellä: {bensa:.0f}\n")

    paivita_location_json(
        valittu[0],
        valittu[1],
        valittu[2][0],
        valittu[2][1],
        bensa
    )

    return (valittu[0], valittu[1], valittu[2]), bensa

# ===============================
# MAIN
# ===============================

if __name__ == "__main__":
    Visuals.logo()

    print("=== FUEL TO FLY ===")
    input("Paina ENTER aloittaaksesi\n")

    nimi, kaikki_kentat, kentta, bensa = alku()
    kayty_kentat = [kentta[0]]

    while bensa > 0:
        kentta, bensa = pelaa_peli(kentta, kaikki_kentat, kayty_kentat, bensa)
        if kentta is None:
            break
        kayty_kentat.append(kentta[0])

    peli_loppu(nimi, kayty_kentat, kokonaismatka=0)
    print("\nPeli päättyi. Kiitos pelaamisesta!")
