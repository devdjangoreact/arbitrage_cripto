// Symbols Management functionality
class SymbolsManager {
  constructor() {
    this.symbolsData = [];
    this.exchangesData = [];
  }

  // Setup symbols modal functionality
  setupSymbolsModal() {
    console.log("Setting up symbols modal...");
    const symbolsBtn = document.getElementById("symbolsBtn");
    const symbolsModal = document.getElementById("symbolsModal");
    const symbolsModalClose = document.getElementById("symbolsModalClose");
    const symbolsSearch = document.getElementById("symbolsSearch");
    const symbolsList = document.getElementById("symbolsList");
    const totalSymbolsCount = document.getElementById("totalSymbolsCount");
    const selectedSymbolsCount = document.getElementById("selectedSymbolsCount");

    let allSymbols = [];
    let selectedSymbols = new Set();
    let filteredSymbols = [];

    // Open modal
    if (symbolsBtn) {
      symbolsBtn.addEventListener("click", function () {
        symbolsModal.classList.add("show");
        this.loadSymbols();
      }.bind(this));
    }

    // Close modal
    if (symbolsModalClose) {
      symbolsModalClose.addEventListener("click", function () {
        symbolsModal.classList.remove("show");
      });
    }

    // Close modal when clicking outside
    if (symbolsModal) {
      symbolsModal.addEventListener("click", function (e) {
        if (e.target === symbolsModal) {
          symbolsModal.classList.remove("show");
        }
      });
    }

    // Search functionality
    if (symbolsSearch) {
      symbolsSearch.addEventListener("input", function () {
        const searchTerm = this.value.toLowerCase();
        filteredSymbols = allSymbols.filter((symbol) =>
          symbol.toLowerCase().includes(searchTerm)
        );
        this.renderSymbols();
      }.bind(this));
    }

    // Load symbols from API data
    this.loadSymbols = function() {
      fetch("/api/data")
        .then((response) => response.json())
        .then((data) => {
          allSymbols = [];
          for (const [exchange, tokens] of Object.entries(data)) {
            for (const symbol of Object.keys(tokens)) {
              if (!allSymbols.includes(symbol)) {
                allSymbols.push(symbol);
              }
            }
          }
          allSymbols.sort();
          filteredSymbols = [...allSymbols];
          if (totalSymbolsCount)
            totalSymbolsCount.textContent = allSymbols.length;
          this.renderSymbols();
        })
        .catch((error) => {
          console.error("Error loading symbols:", error);
          allSymbols = [];
          filteredSymbols = [];
          this.renderSymbols();
        });
    }.bind(this);

    // Render symbols list
    this.renderSymbols = function() {
      if (!symbolsList) return;
      symbolsList.innerHTML = "";
      filteredSymbols.forEach((symbol) => {
        const symbolItem = document.createElement("div");
        symbolItem.className = "symbol-item";
        if (selectedSymbols.has(symbol)) {
          symbolItem.classList.add("selected");
        }
        symbolItem.textContent = symbol.toUpperCase();
        symbolItem.addEventListener("click", function () {
          this.toggleSymbol(symbol);
        }.bind(this));
        symbolsList.appendChild(symbolItem);
      });
      this.updateSelectedCount();
    }.bind(this);

    // Toggle symbol selection
    this.toggleSymbol = function(symbol) {
      if (selectedSymbols.has(symbol)) {
        selectedSymbols.delete(symbol);
      } else {
        selectedSymbols.add(symbol);
      }
      this.renderSymbols();
    }.bind(this);

    // Update selected count
    this.updateSelectedCount = function() {
      if (selectedSymbolsCount)
        selectedSymbolsCount.textContent = selectedSymbols.size;
    }.bind(this);
  }

  // Load symbols data
  loadSymbolsData() {
    fetch("/api/symbols")
      .then((response) => response.json())
      .then((result) => {
        if (result.status === "success") {
          this.symbolsData = result.data;
          this.renderSymbolsTable();
        } else {
          console.error("Error loading symbols:", result.message);
        }
      })
      .catch((error) => {
        console.error("Error loading symbols:", error);
      });
  }

  // Load exchanges data
  loadExchangesData() {
    fetch("/api/exchanges")
      .then((response) => response.json())
      .then((result) => {
        if (result.status === "success") {
          this.exchangesData = result.data;
          this.renderExchangesTable();
        } else {
          console.error("Error loading exchanges:", result.message);
        }
      })
      .catch((error) => {
        console.error("Error loading exchanges:", error);
      });
  }

  // Render symbols table
  renderSymbolsTable() {
    const pairsTableBody = document.getElementById("pairsTableBody");
    if (!pairsTableBody) return;

    pairsTableBody.innerHTML = "";
    this.symbolsData.forEach((symbol, index) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td class="pair-symbol">${symbol.symbol}</td>
        <td>
          <input
            type="checkbox"
            class="pair-checkbox"
            ${symbol.use ? "checked" : ""}
            data-index="${index}"
          />
        </td>
      `;
      pairsTableBody.appendChild(row);
    });

    // Add event listeners to checkboxes
    const checkboxes = pairsTableBody.querySelectorAll(".pair-checkbox");
    checkboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", function () {
        const index = parseInt(this.dataset.index);
        this.symbolsData[index].use = this.checked;
        this.updateSymbolsData();
      }.bind(this));
    }.bind(this));
  }

  // Render exchanges table
  renderExchangesTable() {
    const exchangesTableBody = document.getElementById("exchangesTableBody");
    if (!exchangesTableBody) return;

    exchangesTableBody.innerHTML = "";
    this.exchangesData.forEach((exchange, index) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td class="exchange-name">${exchange.exchange}</td>
        <td>
          <input
            type="checkbox"
            class="exchange-checkbox"
            ${exchange.use ? "checked" : ""}
            data-index="${index}"
          />
        </td>
      `;
      exchangesTableBody.appendChild(row);
    });

    // Add event listeners to checkboxes
    const checkboxes =
      exchangesTableBody.querySelectorAll(".exchange-checkbox");
    checkboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", function () {
        const index = parseInt(this.dataset.index);
        this.exchangesData[index].use = this.checked;
        this.updateExchangesData();
      }.bind(this));
    }.bind(this));
  }

  // Update symbols data on server
  updateSymbolsData() {
    fetch("/api/symbols", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ symbols: this.symbolsData }),
    })
      .then((response) => response.json())
      .then((result) => {
        if (result.status === "success") {
          console.log("Symbols updated successfully");
        } else {
          console.error("Error updating symbols:", result.message);
        }
      })
      .catch((error) => {
        console.error("Error updating symbols:", error);
      });
  }

  // Update exchanges data on server
  updateExchangesData() {
    fetch("/api/exchanges", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ exchanges: this.exchangesData }),
    })
      .then((response) => response.json())
      .then((result) => {
        if (result.status === "success") {
          console.log("Exchanges updated successfully");
        } else {
          console.error("Error updating exchanges:", result.message);
        }
      })
      .catch((error) => {
        console.error("Error updating exchanges:", error);
      });
  }
}

// Create global symbols manager instance
window.symbolsManager = new SymbolsManager();
