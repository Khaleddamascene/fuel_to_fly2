// --- Hakee backendiltä 3 lähintä lentokenttää ---
async function haePeliValinnat() {
  try {
    const bodyData = {
      lat: window.currentLat || 60.1699,
      lon: window.currentLon || 24.9384,
      kayty_kentat: window.kaytyKentat || []
    };

    console.log("Lähetetään backendille:", bodyData);

    const response = await fetch("http://localhost:5000/api/peli_valinnat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bodyData),
    });

    if (!response.ok) throw new Error("HTTP ERROR: " + response.status);

    const data = await response.json();
    console.log("Backend palautti:", data);

    if (!data.choices || data.choices.length === 0) {
      console.warn("Backend ei palauttanut kenttiä!");
      return;
    }

    naytaValinnat(data.choices);

  } catch (err) {
    console.error("Virhe haePeliValinnat():", err);
  }
}

// --- Näyttää 3 lohkoon lentokentät ---
function naytaValinnat(valinnat) {
  const lohkot = document.querySelectorAll(".ajankohtainen_tieto_2_inner");

  lohkot.forEach((lohko, index) => {
    const kentta = valinnat[index];
    if (!kentta) return;

    // täyttö
    lohko.querySelector(".municipality").textContent = kentta.municipality || "-";
    lohko.querySelector(".ident").textContent = kentta.ident || "-";
    lohko.querySelector(".name").textContent = kentta.name || "-";
    lohko.querySelector(".country").textContent = kentta.country || "-";
    lohko.querySelector(".continent").textContent = kentta.continent || "Ei tietoa";

    const nappi = lohko.querySelector(".a2_inner_content_4_button");

    nappi.onclick = () => {
      console.log("Käyttäjä valitsi:", kentta);
      valitseKentta(kentta);
    };
  });
}

// --- Päivittää pelin tilaa kun käyttäjä lentää uuteen kenttään ---
function valitseKentta(kentta) {

  window.currentLat = Number(kentta.lat);
  window.currentLon = Number(kentta.lon);

  if (!window.kaytyKentat.includes(kentta.ident)) {
    window.kaytyKentat.push(kentta.ident);
  }

  console.log("Päivitetty tila:", {
    lat: window.currentLat,
    lon: window.currentLon,
    käyty: window.kaytyKentat
  });

  haePeliValinnat();
}

// --- Alustus kun sivu latautuu ---
document.addEventListener("DOMContentLoaded", () => {
  window.currentLat = 51.47;      // Heathrow
  window.currentLon = -0.4543;
  window.kaytyKentat = [];

  haePeliValinnat();
});
