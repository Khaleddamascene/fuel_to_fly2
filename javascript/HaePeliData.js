// PELIN LOGIIKKA JA DATAKÄSITTELY
class PeliDemo {
  constructor() {
    this.currentState = null;
    this.choices = [];
  }

  // Haetaaan 3 lentokentä valintaa palvelimelta
  async lataaValinnat() {
    try {
      const response = await fetch("http://localhost:5000/api/get_Valinnat");
      console.log("Get_Valinnat response status:", response.status);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Choices data:", data);

      this.choices = data.choices || [];
    } catch (error) {
      console.error("Error loading Valinnat:", error);
      this.naytaVirhe("Valintojen lataus epäonnistui: " + error.message);
    }
  }
  
  //   seraavaksi näytetään valintoja frontendissä peli.html tiedostossa


}
