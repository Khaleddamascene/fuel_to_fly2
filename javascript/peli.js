// Peli sivun kartta Alku
const map = L.map('karta_tieto_div').setView([60.1699, 24.9384], 12); // Tähän pitä laita lat ja lon muuttujat että karta näytä nykyinen paika

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
}).addTo(map);
// Peli sivun kartta Loppu