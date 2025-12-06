import mysql.connector
import random
from geopy.distance import geodesic
import json
import Visuals


def get_connection():
    return mysql.connector.connect(
        host='127.0.0.1',
        port=3307,
        database='fuel_to_fly',
        user='khaled',
        password='1234',
        autocommit=True
    )


# --- JSON APUFUNKTIO ---
def paivita_location_json(ident, name, lat, lon, fuel):
    with open("location.json", "w") as f:
        json.dump({
            "lat": lat,
            "lon": lon,
            "ident": ident,
            "name": name,
            "fuel": fuel
        }, f)

def reset_location_file():
    paivita_location_json(0, "peli ei ole alkanut", 60.1699, 24.9384, 1000)

reset_location_file()

# --- KOMENNOT ---
komennot = [
    (["apua", "h", "a", "komennot"], "apua", "Näytä kaikki komennot"),
    (["ohje", "ohjeet", "o"], "ohje", "Näytä pelin ohjeet")
]

# --- OHJEET ---
def Ohjeet():
    print("\nOhjeet:")
    print("Sinulle annetaan kolme vaihtoehtoista lentokenttää:")
    print("- Lähin kenttä: turvallisin, saat lisää polttoainetta (+200).")
    print("- Keskikenttä: tasapainoinen valinta, ei lisäpolttoainetta.")
    print("- Kaukaisin kenttä: riski, kuluttaa paljon polttoainetta.")
    print("Jos polttoaine loppuu, peli päättyy.")
    input("Paina ENTER jatkaaksesi...")

# --- KOMENTOKÄSITTELY ---
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

    nimi = input("Syötä pelaajan nimi: ").strip()
    while not nimi:
        nimi = input("Nimi ei voi olla tyhjä. Anna nimi: ").strip()

    aloitus = random.choice(kaikki_kentat)
    pelaaja_ident, pelaaja_nimi, lat, lon, municipality, country_name = aloitus
    bensa = 1000.0

    print(f"\nTervetuloa peliin, {nimi}!")
    print(f"Aloitat kentältä: {pelaaja_nimi} ({pelaaja_ident})")
    print(f"Polttoainetta käytössäsi: {bensa:.0f} yksikköä.\n")

    cursor.close()
    yhteys.close()

    paivita_location_json(pelaaja_ident, pelaaja_nimi, lat, lon, bensa)

    return nimi, kaikki_kentat, (pelaaja_ident, pelaaja_nimi, (lat, lon)), bensa

# --- PELIN PÄÄOSA ---
def pelaa_peli(pelaaja_kentta, kaikki_kentat, kayty_kentat, bensa):
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
        return pelaaja_kentta, bensa, 0

    kentta_etaisyydet.sort(key=lambda x: x[2])
    lahin, keskimmainen, kaukaisin = kentta_etaisyydet[0], kentta_etaisyydet[len(kentta_etaisyydet)//2], kentta_etaisyydet[-1]
    jarjestetyt = [lahin, keskimmainen, kaukaisin]

    vaihtoehdot = jarjestetyt.copy()
    random.shuffle(vaihtoehdot)

    print("Vaihtoehtoiset lentokentät:")
    for i, (ident, name, dist, sijainti, municipality, country) in enumerate(vaihtoehdot, start=1):
        print(f"{i}. Kaupunki: {municipality}")
        print(f"   Lentokenttäkoodi: {ident}")
        print(f"   Lentokenttä: {name}")
        print(f"   Maa: {country}\n")

    # Valinta
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
        reset_location_file()
        return pelaaja_kentta, 0, 0

    bensa -= matka

    if valittu == jarjestetyt[0]:
        print("Turvallinen valinta! Saat lisää polttoainetta (+200).")
        bensa += 200
    elif valittu == jarjestetyt[1]:
        print("Keskipitkä lento onnistui hyvin.")
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
            kentta, bensa, matka = pelaa_peli(kentta, kaikki_kentat, kayty_kentat, bensa)
            if bensa > 0:
                kayty_kentat.append(kentta[0])
                kokonaismatka += matka

        while True:
            uusiksi = input("Haluatko jatkaa? (Kyllä/Ei) ").lower().strip()
            if uusiksi in ("kyllä", "k"):
                break
            elif uusiksi in ("ei", "e"):
                peliJatkuu = False
                break

        # Tallennetaan tulokset tietokantaan
        yhteys = get_connection()
        cursor = yhteys.cursor()

        sql = "INSERT INTO results (player_name, visited_count, total_distance) VALUES (%s, %s, %s)"
        values = (nimi, len(kayty_kentat), kokonaismatka)
        cursor.execute(sql, values)
        yhteys.commit()

        print(f"\nSinä {nimi} vierailit {len(kayty_kentat)} kentässä ja lensit yhteensä {kokonaismatka:.2f} km\n")

        # Paras tulos kenttien mukaan
        cursor.execute(
            "SELECT player_name, visited_count, total_distance FROM results ORDER BY visited_count DESC, total_distance DESC LIMIT 1")
        best_by_airports = cursor.fetchone()
        if best_by_airports and best_by_airports[0] == nimi:
            print("! Congratulations New Record! Vierailit eniten lentokenttiä")
        print(f"Eniten kenttiä: {best_by_airports[0]} vieraili {best_by_airports[1]} kentässä ja lensi {best_by_airports[2]:.2f} km\n")

        # Paras matkan pituuden mukaan
        cursor.execute(
            "SELECT player_name, visited_count, total_distance FROM results ORDER BY total_distance DESC, visited_count DESC LIMIT 1")
        best_by_distance = cursor.fetchone()
        if best_by_distance and best_by_distance[0] == nimi:
            print("! Congratulations New Record! Lensit pisimmän matkan")
        print(f"Isoin matka: {best_by_distance[0]} vieraili {best_by_distance[1]} kentässä ja lensi {best_by_distance[2]:.2f} km\n")

        cursor.close()
        yhteys.close()
