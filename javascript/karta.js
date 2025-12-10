async function haeSijainnitTeeKartta() {
    try{
        const response = await fetch('http://localhost:5000/api/location');
        console.log("location.json test", response)
        console.log("Vastaus saatu, status:", response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP server error! status: ${response.status}`);
        }
        
        const sijaintiData = await response.json();
        console.log("Sijaintidata:", sijaintiData);
        
        luoKartta(sijaintiData.lat, sijaintiData.lon, sijaintiData.name, sijaintiData.fuel);
    } catch(error){
        console.error("Virhe haettaessa sijaintitietoja:", error);
        console.log("Käytetään oletussijaintia.");
        // Oletussijainti (Helsinki)
        luoKartta(60.1699, 24.9384, "Peli ei toimi", 0);
    }
}

function luoKartta(lat, lon, name, fuel) {
    const karta_div = document.getElementById('karta_tieto_div');
    const current_airport = document.getElementById('current_airport');
    const fuel_left = document.getElementById('fuel_left');

    if (name == "peli päättynyt") {
        window.location.href = "kun_peli_haviaa.html";
        return
    }
    
    if (!karta_div) {
        console.error("Kartta-diviä ei löydy!");
        return;
    }
    
    if (!current_airport){
        console.log("teksti kenttää ei löydy!");
        return;
    }
    
    if (!fuel_left){
        console.log("Polttoainekenttää ei löydy!");
        return;
    }
    
    current_airport.textContent = name;
    fuel_left.textContent = `${fuel} Yksikköä`;
    
    karta_div.innerHTML = ``;
    
    const map = L.map('karta_tieto_div').setView([lat, lon], 10);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap',
        maxZoom: 18,
    }).addTo(map);
    
    L.marker([lat, lon]).addTo(map)
        .bindPopup(name)
        .openPopup();
    
    console.log("Kartta luotu onnistuneesti!");
    window.peliKartta = map; // Tallennetaan kartta globaaliksi, jos tarvitaan myöhemmin
}

document.addEventListener("DOMContentLoaded", function() {
    haeSijainnitTeeKartta();
});

// ================================
// HAE LENTOKENTTÄVALINNAT
// ================================
const VALINNAT_API = "http://localhost:5000/api/get_valinnat";

document.addEventListener("DOMContentLoaded", () => {
    console.log("DOMContentLoaded OK");
    haeValinnat();
});

async function haeValinnat() {
    try {
        console.log("Haetaan:", VALINNAT_API);

        const res = await fetch(VALINNAT_API);
        const data = await res.json();

        console.log("Saatiin data:", data);

        if (!data.choices || !Array.isArray(data.choices)) {
            console.warn("choices puuttuu tai ei ole lista");
            return;
        }

        const fuelEl = document.getElementById("fuel_left");
        if (fuelEl && data.fuel !== undefined) {
            fuelEl.textContent = `${data.fuel} yksikköä`;
        }

        const lohkot = document.querySelectorAll(".ajankohtainen_tieto_2_inner");
        console.log("Lohkoja:", lohkot.length);

        data.choices.forEach((airport, index) => {
            const lohko = lohkot[index];
            if (!lohko) return;

            lohko.querySelector(".municipality").textContent = airport.municipality ?? "—";
            lohko.querySelector(".ident").textContent        = airport.ident ?? "—";
            lohko.querySelector(".name").textContent         = airport.name ?? "—";
            lohko.querySelector(".country").textContent      = airport.country ?? "—";
            lohko.querySelector(".continent").textContent    = airport.continent ?? "—";
        });

    } catch (err) {
        console.error("Virhe valintoja haettaessa:", err);
    }
}

// ================================
// VALITSE LENTOKENTTÄ
// ================================
const VALITSE_API = "http://localhost:5000/api/valitse_kentta";
document.querySelectorAll(".a2_inner_content_4_button").forEach((btn, index) => {
    btn.addEventListener("click", async () => {
        console.log("Klikattiin nappia, index:", index + 1);
        const res = await fetch(VALITSE_API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ choice_index: index }) // 0,1,2
        });
        const data = await res.json();
        console.log("Backend vastasi:", data);
    });
});

// ================================
// AUTOMAATTINEN PELIN LOPPUSEURANTA
// ================================
async function tarkistaPelinLoppu() {
    try {
        const res = await fetch("http://localhost:5000/api/location");
        if (!res.ok) return;

        const data = await res.json();

        // Tarkista, onko peli loppunut
        if (data.game_over) {
            console.log("Peli päättyi!");
            alert("Peli päättyi! Siirrytään tulokset-sivulle.");
            window.location.href = "/kun_peli_haviaa.html"; // oma tulossivu
        }
    } catch (err) {
        console.error("Virhe pelin tilan haussa:", err);
    }
}
// Käynnistetään tarkistus joka 0.5 sekuntia, karttaa ei kosketa
setInterval(tarkistaPelinLoppu, 500);