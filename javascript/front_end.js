'use strict';

document.addEventListener("DOMContentLoaded", () => {
    const startForm = document.getElementById("startForm");
    const playerNameInput = document.getElementById("playerName");
    if (!startForm) return;

    startForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const playerName = playerNameInput.value.trim();

        if (playerName === "") {
            alert("Syötä pelaajan nimi ennen aloitusta!");
            return;
        }

        try {
            // 1) Start the game process (if not already started)
            const token = localStorage.getItem('START_TOKEN') || null;
            const startResp = await fetch('http://localhost:5000/api/start_game', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: token })
            });

            if (!startResp.ok) {
                const err = await startResp.json().catch(() => ({}));
                throw new Error('Palvelin ei sallinut käynnistystä: ' + (err.error || startResp.status));
            }

            await startResp.json();

            // 2) Insert player into database
            const response = await fetch("http://localhost:5000/api/pelaaja", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ player_name: playerName }),
            });

            if (!response.ok) {
                throw new Error("Pelaajan lisääminen epäonnistui.");
            }

            const result = await response.json();
            console.log(result.message);
            localStorage.setItem("pelaajan_nimi", playerName);

            // 3) Send the name to the running paaohjelma process
            const sendResp = await fetch('http://localhost:5000/api/send_name', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ player_name: playerName, start_if_missing: true })
            });

            if (!sendResp.ok) {
                const err = await sendResp.json().catch(() => ({}));
                throw new Error('Nimen lähetys epäonnistui: ' + (err.error || sendResp.status));
            }

            const sendData = await sendResp.json();
            console.log('send_name response', sendData);

            // 4) Navigate to game page
            window.location.href = "peli.html";

        } catch (error) {
            console.error("Virhe:", error);
            alert(error.message || "Virhe pelaajan käsittelyssä. Tarkista palvelin.");
        }
    });
});


    // Tämä Function hakee tulokset Flask-palvelimelta ja päivittää HTML-taulukot

async function HaeTuloksetFun() {
    try {
        const response = await fetch('http://localhost:5000/api/tulokset');
        const results = await response.json();
        
        // Haetaan top 5 pelaajaa eniten kenttiä vierailtu ja pisin matka
        const EnitenKenttiä = [...results].sort((a, b) => 
            b.visited_count - a.visited_count || b.total_distance - a.total_distance
        ).slice(0, 5);
        
        // Haetaan top 5 pelaajaa pisin matka ja eniten kenttiä vierailtu
        const IsoinMatka = [...results].sort((a, b) => 
            b.total_distance - a.total_distance || b.visited_count - a.visited_count
        ).slice(0, 5);
        
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

// Aloita peli -napin käsittelijä: yritä käynnistää paikallinen peli-palveluprosessi
document.addEventListener("DOMContentLoaded", () => {
    const aloitaBtn = document.getElementById('aloita_peli');
    if (!aloitaBtn) return;

    aloitaBtn.addEventListener('click', async (e) => {
        // estä oletusnavigointi (nappi on linkin sisällä)
        e.preventDefault();

        const anchor = aloitaBtn.closest('a');

        try {
            // Lähetetään pyyntö backendille käynnistää peli
            const token = localStorage.getItem('START_TOKEN') || null;
            const resp = await fetch('http://localhost:5000/api/start_game', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: token })
            });

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                alert('Palvelin ei sallinut käynnistystä: ' + (err.error || resp.status));
                return;
            }

            const data = await resp.json();
            console.log('start_game response', data);

            // Jos kaikki ok, siirry seuraavalle sivulle (nimen syöttö)
            if (anchor && anchor.getAttribute('href')) {
                window.location.href = anchor.getAttribute('href');
            }

        } catch (error) {
            console.error('Virhe käynnistäessä peliä:', error);
            alert('Virhe käynnistäessä peliä. Tarkista palvelin (http://localhost:5000).');
        }
    });
});
