'use strict';

document.addEventListener("DOMContentLoaded", () => {
    const startForm = document.getElementById("startForm");
    const playerNameInput = document.getElementById("playerName");

    startForm.addEventListener("submit", async (e) => {
        e.preventDefault(); // estetään lomakkeen oletusarvoinen lähetys

        const playerName = playerNameInput.value.trim();

        if (playerName === "") {
            alert("Syötä pelaajan nimi ennen aloitusta!");
            return;
        }

        try {
            // Lähetetään nimi Flask-palvelimelle
            const response = await fetch("http://localhost:5000/api/pelaaja", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ player_name: playerName }),
            });

            if (!response.ok) {
                throw new Error("Pelaajan lisääminen epäonnistui.");
            }

            const result = await response.json();
            console.log(result.message);

            localStorage.setItem("pelaajan_nimi", playerName);


            window.location.href = "peli.html";

        } catch (error) {
            console.error("Virhe:", error);
            alert("Virhe pelaajan lisäämisessä. Tarkista palvelin.");
        }
    });
});

    // Tämä Function hakee tulokset Flask-palvelimelta ja päivittää HTML-taulukot

async function HaeTuloksetFun() {
    try {
        const response = await fetch('http://localhost:5000/api/tulokset');
        const results = await response.json();
        
        // Haetaan top 10 pelaajaa eniten kenttiä vierailtu ja pisin matka
        const EnitenKenttiä = [...results].sort((a, b) => 
            b.visited_count - a.visited_count || b.total_distance - a.total_distance
        ).slice(0, 10);
        
        // Haetaan top 10 pelaajaa pisin matka ja eniten kenttiä vierailtu
        const IsoinMatka = [...results].sort((a, b) => 
            b.total_distance - a.total_distance || b.visited_count - a.visited_count
        ).slice(0, 10);
        
        // Päivitetään HTML-taulukot
        const EnitenKenttiäBody = document.getElementById('Eniten_kenttiä-body');
        EnitenKenttiäBody.innerHTML = ''; 

        EnitenKenttiä.forEach(result => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${result.player_name}</td>
                <td>${result.visited_count}</td>
                <td>${parseFloat(result.total_distance).toFixed(2)} km</td>
            `;
            EnitenKenttiäBody.appendChild(row);
        });
        
        const IsoinMatkaBody = document.getElementById('Isoin_matka-body');
        IsoinMatkaBody.innerHTML = ''; 
        
        IsoinMatka.forEach(result => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${result.player_name}</td>
                <td>${result.visited_count}</td>
                <td>${parseFloat(result.total_distance).toFixed(2)} km</td>
            `;
            IsoinMatkaBody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error loading results:', error);
        document.getElementById('Eniten_kenttiä-body').innerHTML = 
            '<tr><td colspan="3">Error loading results. Varmista, että Flask-palvelin on käynnissä..</td></tr>';
        document.getElementById('Isoin_matka-body').innerHTML = 
            '<tr><td colspan="3">Error loading results. Varmista, että Flask-palvelin on käynnissä..</td></tr>';
    }
}


document.addEventListener('DOMContentLoaded', HaeTuloksetFun);

// _____HaeTuloksetFun function Loppu _________________________________


async function HaePelaajaData() {
    try {
        const response = await fetch("http://localhost:5000/api/pelaaja/1");
        const data = await response.json();

        // Hekee viimeisimmän pelaajan tietokannasta
            if (data.length > 0) {
                const viimeinenPelaaja = data[data.length - 1];

            // Haetaan HTML elementit niiden ID:n pelaajan_nimi

                document.getElementById("pelaajan_nimi").textContent = viimeinenPelaaja.player_name || "-";
                document.getElementById("vierailtuja_kenttia").textContent = viimeinenPelaaja.visited_count || "-";
                document.getElementById("kokonaismatka").textContent = (viimeinenPelaaja.total_distance || 0) + " km";
                document.getElementById("kaytetty_bensa").textContent = viimeinenPelaaja.fuel_used || "-";

        } else {
            console.error("Ei pelaajia listassa.");
        }
    // HTML default arvot tai pyyntö epäonnistuu 
    } catch (error) {
        console.error("Virhe datan haussa:", error);
        document.getElementById("pelaajan_nimi").textContent = "Ei dataa";
        document.getElementById("vierailtuja_kenttia").textContent = "-";
        document.getElementById("kokonaismatka").textContent = "- km";
        document.getElementById("kaytetty_bensa").textContent = "-";
    }
}

document.addEventListener("DOMContentLoaded", HaePelaajaData);

// _____HaePelaajaData function Loppu _________________________________