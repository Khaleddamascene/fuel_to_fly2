async function haeSijainnitTeeKartta() {
    try{
        const response = await fetch('http://localhost:5000/api/location');
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