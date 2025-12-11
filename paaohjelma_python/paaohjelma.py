from db import get_connection
import random
from geopy.distance import geodesic
import json
import Visuals
from dotenv import load_dotenv
load_dotenv()

# --- JSON APUFUNKTIOT ---
def paivita_location_json(ident, name, lat, lon, fuel):
    fuel_int = int(fuel)
    with open("location.json", "w", encoding="utf-8") as f:
        json.dump({
            "lat": lat,
            "lon": lon,
            "ident": ident,
            "name": name,
            "fuel": fuel_int
        }, f, ensure_ascii=False)

def reset_location_file():
    paivita_location_json(0, "peli ei ole alkanut", 60.1699, 24.9384, 1000)

VALINNAT_FILE = "valinnat.json"

def tallenna_valinnat_json(vaihtoehdot, fuel):
    data = {"fuel": round(fuel, 0), "choices": []}
    for ident, name, dist, (lat, lon), municipality, country in vaihtoehdot:
        data["choices"].append({
            "ident": ident,
            "name": name,
            "distance": round(dist, 1),
            "latitude": lat,
            "longitude": lon,
            "municipality": municipality,
            "country": country
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


# --- KOMENNOT ---
komennot = [
    (["apua", "h", "a", "komennot"], "apua", "Näytä kaikki komennot"),
    (["ohje", "ohjeet", "o"], "ohje", "Näytä pelin ohjeet")
]

def Ohjeet():
    print("\nOhjeet:")
    print("- Lähin kenttä: turvallisin, saat lisää polttoainetta (+1000).")
    print("- Keskikenttä: tasapainoinen valinta, ei lisäpolttoainetta.")
    print("- Kaukaisin kenttä: riski, kuluttaa paljon polttoainetta.")
    print("Jos polttoaine loppuu, peli päättyy.")
    input("Paina ENTER jatkaaksesi...")

def HaeKomento(komento):
    komento = komento.lower().strip()
    for avainsanat, toiminto, kuvaus in komennot:
        if komento in avainsanat:
            if toiminto == "apua":
                print("\nKomennot:")
                for av, _, kuvaus in komennot:
                    print(f"'{av[0]}' : {kuvaus}")
            elif toiminto == "ohje":
                Ohjeet()
            return True
    return False

def Puhe():
    while True:
        puhe = input("> ").lower().strip()
        if not HaeKomento(puhe):
            return puhe

# --- PELIN ALKU ---
def alku():
    yhteys = get_connection()
    cursor = yhteys.cursor()

    cursor.execute("""
        SELECT a.ident, a.name, a.latitude_deg, a.longitude_deg,
               a.municipality, c.name AS country_name
        FROM airport a
        LEFT JOIN country c ON a.iso_country = c.iso_country
        WHERE a.latitude_deg IS NOT NULL AND a.longitude_deg IS NOT NULL
    """)
    kaikki_kentat = cursor.fetchall()

    nimi = input("Syötä pelaajan nimi: ").strip()
    while not nimi:
        nimi = input("Nimi ei voi olla tyhjä. Anna nimi: ").strip()

    aloitus = random.choice(kaikki_kentat)
    pelaaja_ident, pelaaja_nimi, lat, lon, municipality, country_name = aloitus
    bensa = 1000.0

    print(f"\nTervetuloa peliin, {nimi}! Aloitat kentältä: {pelaaja_nimi} ({pelaaja_ident})")
    print(f"Polttoainetta käytössäsi: {bensa:.0f} yksikköä.\n")

    cursor.close()
    yhteys.close()

    paivita_location_json(pelaaja_ident, pelaaja_nimi, lat, lon, bensa)

    return nimi, kaikki_kentat, (pelaaja_ident, pelaaja_nimi, (lat, lon)), bensa

# 
def get_peli_valinnat(current_lat, current_lon, kayty_kentat):
    yhteys = get_connection()
    cursor = yhteys.cursor()
    cursor.execute("""
        SELECT a.ident,
               a.name,
               a.latitude_deg,
               a.longitude_deg,
               a.municipality,
               c.name AS country_name
        FROM airport a
        LEFT JOIN country c ON a.iso_country = c.iso_country
        WHERE a.latitude_deg IS NOT NULL
          AND a.longitude_deg IS NOT NULL
    """)
    kaikki_kentat = cursor.fetchall()
    cursor.close()
    yhteys.close()

    kentta_etaisyydet = []
    for ident, name, lat, lon, municipality, country in kaikki_kentat:
        if ident in kayty_kentat:
            continue
        matka = geodesic((current_lat, current_lon), (lat, lon)).km
        kentta_etaisyydet.append({
            "ident": ident,
            "name": name,
            "lat": lat,
            "lon": lon,
            "municipality": municipality,
            "country": country,
            "distance": matka
        })

    if len(kentta_etaisyydet) < 3:
        return kentta_etaisyydet  

    
    kentta_etaisyydet.sort(key=lambda x: x["distance"])
    jarjestetyt = [kentta_etaisyydet[0],
                   kentta_etaisyydet[len(kentta_etaisyydet)//2],
                   kentta_etaisyydet[-1]]

  
    vaihtoehdot = jarjestetyt.copy()
    random.shuffle(vaihtoehdot)

    return vaihtoehdot

# --- PELIN PÄÄOSA ---
def pelaa_peli(pelaaja_kentta, kaikki_kentat, kayty_kentat, bensa, nimi, kokonaismatka):
    pelaaja_ident, pelaaja_kentta_nimi, pelaaja_sijainti = pelaaja_kentta
    print(f"\nNykyinen kenttä: {pelaaja_kentta_nimi} ({pelaaja_ident})")

    kentta_etaisyydet = []
    for ident, name, lat, lon, municipality, country in kaikki_kentat:
        if ident == pelaaja_ident or ident in kayty_kentat:
            continue
        matka = geodesic(pelaaja_sijainti, (lat, lon)).km
        kentta_etaisyydet.append((ident, name, matka, (lat, lon), municipality, country))

    if len(kentta_etaisyydet) < 3:
        print("Ei enää uusia kenttiä — peli päättyy!")
        peli_loppu(nimi, kayty_kentat, kokonaismatka)
        return None, 0, 0

    kentta_etaisyydet.sort(key=lambda x: x[2])
    lahin, keskimmainen, kaukaisin = kentta_etaisyydet[0], kentta_etaisyydet[len(kentta_etaisyydet)//2], kentta_etaisyydet[-1]
    jarjestetyt = [lahin, keskimmainen, kaukaisin]

    vaihtoehdot = jarjestetyt.copy()
    random.shuffle(vaihtoehdot)

    tallenna_valinnat_json(vaihtoehdot, bensa)

    print("Vaihtoehtoiset lentokentät:")
    for i, (ident, name, dist, sijainti, municipality, country) in enumerate(vaihtoehdot, start=1):
        print(f"{i}. Kaupunki: {municipality}")
        print(f"   Lentokenttäkoodi: {ident}")
        print(f"   Lentokenttä: {name}")
        print(f"   Maa: {country}\n")

    while True:
        s = input("\nValitse kenttä (1–3): ").strip()
        if HaeKomento(s):
            continue
        try:
            valinta = int(s)
            if 1 <= valinta <= 3:
                break
            print("Valitse numero 1–3.")
        except ValueError:
            print("Anna numero tai komento (esim. 'apua').")

    valittu = vaihtoehdot[valinta - 1]
    matka = valittu[2]

    if bensa < matka:
        print(f"Polttoaine ei riitä lennolle ({matka:.1f} km). Peli päättyy.")
        peli_loppu(nimi, kayty_kentat, kokonaismatka)
        return None, 0, 0

    bensa -= matka
    if valittu == jarjestetyt[0]:
        print("Turvallinen valinta! Saat lisää polttoainetta (+1000).")
        bensa += 1000
    elif valittu == jarjestetyt[1]:
        print("Keskipitkä lento onnistui hyvin.  (+1000)")
        bensa += 1000
    else:
        print("Kaukaisin kenttä! Kulutit paljon polttoainetta.")

    print(f"Lensit {matka:.1f} km. Polttoainetta jäljellä {bensa:.0f}.\n")

    uusi_kentta = (valittu[0], valittu[1], valittu[3])
    paivita_location_json(valittu[0], valittu[1], valittu[3][0], valittu[3][1], bensa)

    return uusi_kentta, bensa, matka

# --- MAIN ---
if __name__ == "__main__":
    Visuals.logo()
    peliJatkuu = True

    while peliJatkuu:
        print("=== Fuel to Fly ===\n")
        input("Paina ENTER aloittaaksesi!\n")
        print("Kirjoita 'ohje' saadaksesi pelin ohjeet.\n")
        Puhe()

        nimi, kaikki_kentat, kentta, bensa = alku()
        kayty_kentat = [kentta[0]]
        kokonaismatka = 0

        while bensa > 0:
            kentta, bensa, matka = pelaa_peli(kentta, kaikki_kentat, kayty_kentat, bensa, nimi, kokonaismatka)
            if kentta is None:
                # Peli loppui automaattisesti
                peliJatkuu = False
                break
            kayty_kentat.append(kentta[0])
            kokonaismatka += matka

        # Tallennetaan lopulliset tulokset tietokantaan, jos peli päättyi kesken
        peli_loppu(nimi, kayty_kentat, kokonaismatka)
        print("Peli päättyi. Kiitos pelaamisesta!")
        break
