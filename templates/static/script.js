// Panel management functionality
document.addEventListener("DOMContentLoaded", function () {
  const menuToggle = document.getElementById("menuToggle");
  const pairsToggle = document.getElementById("pairsToggle");
  const exchangesToggle = document.getElementById("exchangesToggle");
  const ordersToggle = document.getElementById("ordersToggle");
  const analyzerToggle = document.getElementById("analyzerToggle");

  const sidebar = document.getElementById("sidebar");
  const rightSidePanel = document.getElementById("rightSidePanel");
  const pairsPanel = document.getElementById("pairsPanel");
  const exchangesPanel = document.getElementById("exchangesPanel");
  const ordersSection = document.getElementById("ordersSection");
  const analyzerSection = document.getElementById("analyzerSection");
  const dashboardSection = document.getElementById("dashboardSection");
  const arbitrageSection = document.getElementById("arbitrageSection");
  const settingsSection = document.getElementById("settingsSection");
  const exchangesSection = document.getElementById("exchangesSection");
  const logsSection = document.getElementById("logsSection");

  const pairsTableBody = document.getElementById("pairsTableBody");
  const exchangesTableBody = document.getElementById("exchangesTableBody");

  let symbolsData = [];
  let exchangesData = [];
  let ordersData = [];

  // Hide all panels and show sidebar
  function showSidebar() {
    sidebar.classList.remove("collapsed");
    rightSidePanel.classList.remove("show");
    rightSidePanel.classList.add("collapsed");
    pairsPanel.classList.remove("show");
    exchangesPanel.classList.remove("show");
    ordersSection.style.display = "none";
    analyzerSection.style.display = "none";
    pairsToggle.classList.remove("active");
    exchangesToggle.classList.remove("active");
    ordersToggle.classList.remove("active");
    analyzerToggle.classList.remove("active");
  }

  // Toggle right side panel
  function toggleRightSidePanel() {
    if (rightSidePanel.classList.contains("show")) {
      rightSidePanel.classList.remove("show");
      rightSidePanel.classList.add("collapsed");
      pairsPanel.classList.remove("show");
      exchangesPanel.classList.remove("show");
      pairsToggle.classList.remove("active");
      exchangesToggle.classList.remove("active");
    } else {
      rightSidePanel.classList.add("show");
      rightSidePanel.classList.remove("collapsed");
    }
  }

  // Show main content section (Orders, Analyzer) - sidebar stays open
  function showMainSection(section, toggle) {
    rightSidePanel.classList.remove("show");
    rightSidePanel.classList.add("collapsed");
    pairsPanel.classList.remove("show");
    exchangesPanel.classList.remove("show");
    ordersSection.style.display = "none";
    analyzerSection.style.display = "none";
    pairsToggle.classList.remove("active");
    exchangesToggle.classList.remove("active");
    ordersToggle.classList.remove("active");
    analyzerToggle.classList.remove("active");

    if (section) {
      section.style.display = "block";
    }
    toggle.classList.add("active");
  }

  // Show sidebar section
  function showSidebarSection(section) {
    // Hide all sections
    dashboardSection.style.display = "none";
    analyzerSection.style.display = "none";
    arbitrageSection.style.display = "none";
    settingsSection.style.display = "none";
    exchangesSection.style.display = "none";
    logsSection.style.display = "none";
    ordersSection.style.display = "none";

    // Hide right panels
    rightSidePanel.classList.remove("show");
    rightSidePanel.classList.add("collapsed");
    pairsPanel.classList.remove("show");
    exchangesPanel.classList.remove("show");

    // Remove active states from all toggles
    pairsToggle.classList.remove("active");
    exchangesToggle.classList.remove("active");
    ordersToggle.classList.remove("active");
    analyzerToggle.classList.remove("active");

    // Show selected section
    if (section) {
      section.style.display = "block";
    }
  }

  // Hide sidebar and other panels, show specific panel
  function showPanel(panel, toggle) {
    sidebar.classList.add("collapsed");
    pairsPanel.classList.remove("show");
    exchangesPanel.classList.remove("show");
    ordersSection.style.display = "none";
    analyzerSection.style.display = "none";
    pairsToggle.classList.remove("active");
    exchangesToggle.classList.remove("active");
    ordersToggle.classList.remove("active");
    analyzerToggle.classList.remove("active");

    if (panel) {
      panel.classList.add("show");
    } else if (toggle === ordersToggle) {
      ordersSection.style.display = "block";
    } else if (toggle === analyzerToggle) {
      analyzerSection.style.display = "block";
    }
    toggle.classList.add("active");
  }

  // Sidebar toggle - only collapse/expand sidebar
  menuToggle.addEventListener("click", function () {
    sidebar.classList.toggle("collapsed");
  });

  // Pairs panel toggle
  pairsToggle.addEventListener("click", function () {
    if (
      rightSidePanel.classList.contains("show") &&
      pairsPanel.classList.contains("show")
    ) {
      // If right panel is open and showing pairs, close it
      toggleRightSidePanel();
    } else if (
      rightSidePanel.classList.contains("show") &&
      exchangesPanel.classList.contains("show")
    ) {
      // If right panel is open but showing exchanges, switch to pairs
      exchangesPanel.classList.remove("show");
      exchangesToggle.classList.remove("active");
      pairsPanel.classList.add("show");
      pairsToggle.classList.add("active");
      loadSymbolsData();
    } else {
      // Open right panel with pairs
      rightSidePanel.classList.add("show");
      rightSidePanel.classList.remove("collapsed");
      exchangesPanel.classList.remove("show");
      exchangesToggle.classList.remove("active");
      pairsPanel.classList.add("show");
      pairsToggle.classList.add("active");
      loadSymbolsData();
    }
  });

  // Exchanges panel toggle
  exchangesToggle.addEventListener("click", function () {
    if (
      rightSidePanel.classList.contains("show") &&
      exchangesPanel.classList.contains("show")
    ) {
      // If right panel is open and showing exchanges, close it
      toggleRightSidePanel();
    } else if (
      rightSidePanel.classList.contains("show") &&
      pairsPanel.classList.contains("show")
    ) {
      // If right panel is open but showing pairs, switch to exchanges
      pairsPanel.classList.remove("show");
      pairsToggle.classList.remove("active");
      exchangesPanel.classList.add("show");
      exchangesToggle.classList.add("active");
      loadExchangesData();
    } else {
      // Open right panel with exchanges
      rightSidePanel.classList.add("show");
      rightSidePanel.classList.remove("collapsed");
      pairsPanel.classList.remove("show");
      pairsToggle.classList.remove("active");
      exchangesPanel.classList.add("show");
      exchangesToggle.classList.add("active");
      loadExchangesData();
    }
  });

  // Orders section toggle
  ordersToggle.addEventListener("click", function () {
    if (ordersSection.style.display === "block") {
      ordersSection.style.display = "none";
      ordersToggle.classList.remove("active");
    } else {
      showMainSection(ordersSection, ordersToggle);
      loadOrdersData();
    }
  });

  // Analyzer section toggle
  analyzerToggle.addEventListener("click", function () {
    if (analyzerSection.style.display === "block") {
      analyzerSection.style.display = "none";
      analyzerToggle.classList.remove("active");
    } else {
      showMainSection(analyzerSection, analyzerToggle);
      loadTokensData();
    }
  });

  // Load symbols data
  function loadSymbolsData() {
    fetch("/api/symbols")
      .then((response) => response.json())
      .then((result) => {
        if (result.status === "success") {
          symbolsData = result.data;
          renderSymbolsTable();
        } else {
          console.error("Error loading symbols:", result.message);
        }
      })
      .catch((error) => {
        console.error("Error loading symbols:", error);
      });
  }

  // Load exchanges data
  function loadExchangesData() {
    fetch("/api/exchanges")
      .then((response) => response.json())
      .then((result) => {
        if (result.status === "success") {
          exchangesData = result.data;
          renderExchangesTable();
        } else {
          console.error("Error loading exchanges:", result.message);
        }
      })
      .catch((error) => {
        console.error("Error loading exchanges:", error);
      });
  }

  // Render symbols table
  function renderSymbolsTable() {
    pairsTableBody.innerHTML = "";
    symbolsData.forEach((symbol, index) => {
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
        symbolsData[index].use = this.checked;
        updateSymbolsData();
      });
    });
  }

  // Render exchanges table
  function renderExchangesTable() {
    exchangesTableBody.innerHTML = "";
    exchangesData.forEach((exchange, index) => {
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
        exchangesData[index].use = this.checked;
        updateExchangesData();
      });
    });
  }

  // Update symbols data on server
  function updateSymbolsData() {
    fetch("/api/symbols", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ symbols: symbolsData }),
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
  function updateExchangesData() {
    fetch("/api/exchanges", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ exchanges: exchangesData }),
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

  // Load orders data
  function loadOrdersData() {
    fetch("/api/orders")
      .then((response) => response.json())
      .then((result) => {
        if (result.status === "success") {
          ordersData = result.data;
          renderOrdersTable();
        } else {
          console.error("Error loading orders:", result.message);
        }
      })
      .catch((error) => {
        console.error("Error loading orders:", error);
      });
  }

  // Orders filter event listeners
  document.addEventListener("DOMContentLoaded", function () {
    // Apply filters button
    const applyFiltersBtn = document.getElementById("applyFiltersBtn");
    if (applyFiltersBtn) {
      applyFiltersBtn.addEventListener("click", function () {
        renderOrdersTable();
      });
    }

    // Clear filters button
    const clearFiltersBtn = document.getElementById("clearFiltersBtn");
    if (clearFiltersBtn) {
      clearFiltersBtn.addEventListener("click", function () {
        // Clear all filter inputs
        const dateFrom = document.getElementById("dateFrom");
        const dateTo = document.getElementById("dateTo");
        const exchangeFilter = document.getElementById("exchangeFilter");
        const pairFilter = document.getElementById("pairFilter");
        const onlyActiveFilter = document.getElementById("onlyActiveFilter");

        if (dateFrom) dateFrom.value = "";
        if (dateTo) dateTo.value = "";
        if (exchangeFilter) exchangeFilter.value = "";
        if (pairFilter) pairFilter.value = "";
        if (onlyActiveFilter) onlyActiveFilter.checked = false;

        // Re-render table
        renderOrdersTable();
      });
    }

    // Auto-apply filters on input change
    const filterInputs = document.querySelectorAll(
      "#dateFrom, #dateTo, #exchangeFilter, #pairFilter, #onlyActiveFilter"
    );
    filterInputs.forEach((input) => {
      if (input) {
        input.addEventListener("change", function () {
          renderOrdersTable();
        });
      }
    });
  });

  // Sidebar menu event listeners
  document.addEventListener("DOMContentLoaded", function () {
    // Dashboard
    const dashboardLink = document.querySelector('a[href="#"]:first-of-type');
    if (dashboardLink) {
      dashboardLink.addEventListener("click", function (e) {
        e.preventDefault();
        showSidebarSection(dashboardSection);
        // Update active state
        document
          .querySelectorAll(".sidebar-menu a")
          .forEach((link) => link.classList.remove("active"));
        this.classList.add("active");
      });
    }

    // Analyzer
    const analyzerLink = document.querySelectorAll(".sidebar-menu a")[1];
    if (analyzerLink) {
      analyzerLink.addEventListener("click", function (e) {
        e.preventDefault();
        showSidebarSection(analyzerSection);
        // Update active state
        document
          .querySelectorAll(".sidebar-menu a")
          .forEach((link) => link.classList.remove("active"));
        this.classList.add("active");
      });
    }

    // Arbitrage
    const arbitrageLink = document.querySelectorAll(".sidebar-menu a")[2];
    if (arbitrageLink) {
      arbitrageLink.addEventListener("click", function (e) {
        e.preventDefault();
        showSidebarSection(arbitrageSection);
        // Update active state
        document
          .querySelectorAll(".sidebar-menu a")
          .forEach((link) => link.classList.remove("active"));
        this.classList.add("active");
      });
    }

    // Exchanges
    const exchangesLink = document.querySelectorAll(".sidebar-menu a")[3];
    if (exchangesLink) {
      exchangesLink.addEventListener("click", function (e) {
        e.preventDefault();
        showSidebarSection(exchangesSection);
        // Update active state
        document
          .querySelectorAll(".sidebar-menu a")
          .forEach((link) => link.classList.remove("active"));
        this.classList.add("active");
      });
    }

    // Settings
    const settingsLink = document.querySelectorAll(".sidebar-menu a")[4];
    if (settingsLink) {
      settingsLink.addEventListener("click", function (e) {
        e.preventDefault();
        showSidebarSection(settingsSection);
        // Update active state
        document
          .querySelectorAll(".sidebar-menu a")
          .forEach((link) => link.classList.remove("active"));
        this.classList.add("active");
      });
    }

    // Logs
    const logsLink = document.querySelectorAll(".sidebar-menu a")[5];
    if (logsLink) {
      logsLink.addEventListener("click", function (e) {
        e.preventDefault();
        showSidebarSection(logsSection);
        // Update active state
        document
          .querySelectorAll(".sidebar-menu a")
          .forEach((link) => link.classList.remove("active"));
        this.classList.add("active");
      });
    }
  });

  // Render orders accordion
  function renderOrdersTable() {
    const accordion = document.getElementById("ordersAccordion");
    accordion.innerHTML = "";

    // Get filter values
    const dateFrom = document.getElementById("dateFrom")?.value;
    const dateTo = document.getElementById("dateTo")?.value;
    const exchangeFilter = document.getElementById("exchangeFilter")?.value;
    const pairFilter = document.getElementById("pairFilter")?.value;
    const onlyActive = document.getElementById("onlyActiveFilter")?.checked;

    ordersData.forEach((symbolData) => {
      const symbol = symbolData.symbol;

      // Apply pair filter
      if (
        pairFilter &&
        !symbol.toLowerCase().includes(pairFilter.toLowerCase())
      ) {
        return;
      }

      // Count orders for stats
      const ordersCount = symbolData.active?.orders?.length || 0;
      const positionsCount = symbolData.active?.positions?.length || 0;
      const closedCount = symbolData.closed?.length || 0;

      // Create accordion item
      const accordionItem = document.createElement("div");
      accordionItem.className = "accordion-item";
      accordionItem.innerHTML = `
        <div class="accordion-header" data-symbol="${symbol}">
          <div class="accordion-pair-info">
            <div class="accordion-pair-symbol">${symbol}</div>
            <div class="accordion-pair-stats">
              <span>📋 Orders: ${ordersCount}</span>
              <span>📈 Positions: ${positionsCount}</span>
              <span>✅ Closed: ${closedCount}</span>
            </div>
          </div>
          <button class="accordion-toggle">▼</button>
        </div>
        <div class="accordion-content">
          <div class="accordion-tabs">
            <button class="accordion-tab active" data-tab="orders" data-symbol="${symbol}">Orders</button>
            <button class="accordion-tab" data-tab="positions" data-symbol="${symbol}">Positions</button>
            <button class="accordion-tab" data-tab="closed" data-symbol="${symbol}">Closed</button>
          </div>
          <div class="accordion-table-container">
            <table class="accordion-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Exchange</th>
                  <th>Side</th>
                  <th>Type</th>
                  <th>Price</th>
                  <th>Amount</th>
                  <th>Leverage</th>
                  <th>Stop Loss</th>
                  <th>Take Profit</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody class="accordion-table-body" data-symbol="${symbol}">
                <!-- Orders will be loaded here -->
              </tbody>
            </table>
          </div>
        </div>
      `;

      accordion.appendChild(accordionItem);

      // Add event listeners
      const header = accordionItem.querySelector(".accordion-header");
      const content = accordionItem.querySelector(".accordion-content");
      const tabs = accordionItem.querySelectorAll(".accordion-tab");

      header.addEventListener("click", function () {
        const isActive = content.classList.contains("active");

        // Close all other accordion items
        document.querySelectorAll(".accordion-content").forEach((item) => {
          item.classList.remove("active");
        });
        document.querySelectorAll(".accordion-header").forEach((item) => {
          item.classList.remove("active");
        });

        // Toggle current item
        if (!isActive) {
          content.classList.add("active");
          header.classList.add("active");
          // Load default tab (orders)
          loadAccordionTab(symbol, "orders");
        }
      });

      // Tab click handlers
      tabs.forEach((tab) => {
        tab.addEventListener("click", function () {
          const tabType = this.dataset.tab;

          // Update active tab
          tabs.forEach((t) => t.classList.remove("active"));
          this.classList.add("active");

          // Load tab content
          loadAccordionTab(symbol, tabType);
        });
      });
    });
  }

  // Load accordion tab content
  function loadAccordionTab(symbol, tabType) {
    const tbody = document.querySelector(
      `.accordion-table-body[data-symbol="${symbol}"]`
    );
    tbody.innerHTML = "";

    const symbolData = ordersData.find((data) => data.symbol === symbol);
    if (!symbolData) return;

    // Get filter values
    const dateFrom = document.getElementById("dateFrom")?.value;
    const dateTo = document.getElementById("dateTo")?.value;
    const exchangeFilter = document.getElementById("exchangeFilter")?.value;

    let items = [];

    if (tabType === "orders" && symbolData.active?.orders) {
      items = symbolData.active.orders;
    } else if (tabType === "positions" && symbolData.active?.positions) {
      items = symbolData.active.positions;
    } else if (tabType === "closed" && symbolData.closed) {
      items = symbolData.closed;
    }

    items.forEach((item, index) => {
      // Apply filters
      if (exchangeFilter && item.exchange !== exchangeFilter) {
        return;
      }

      if (dateFrom && item.date && new Date(item.date) < new Date(dateFrom)) {
        return;
      }

      if (dateTo && item.date && new Date(item.date) > new Date(dateTo)) {
        return;
      }

      const row = createAccordionOrderRow(item, symbol, tabType, index);
      tbody.appendChild(row);
    });
  }

  // Create accordion order row
  function createAccordionOrderRow(order, symbol, type, index) {
    const row = document.createElement("tr");

    // Format date
    const orderDate = order.date
      ? new Date(order.date).toLocaleDateString()
      : "-";

    row.innerHTML = `
      <td class="order-date">${orderDate}</td>
      <td>${order.exchange.toUpperCase()}</td>
      <td><span class="order-side ${
        order.side
      }">${order.side.toUpperCase()}</span></td>
      <td><span class="order-type">${order.type.toUpperCase()}</span></td>
      <td>${order.price}</td>
      <td>${order.amount}</td>
      <td>${order.leverage}x</td>
      <td>${order.stop_loss || "-"}</td>
      <td>${order.take_profit || "-"}</td>
      <td class="order-actions">
        <button class="order-btn edit" onclick="editOrder('${symbol}', '${type}', ${index})">Edit</button>
        <button class="order-btn close" onclick="closeOrder('${symbol}', '${type}', ${index})">Close</button>
        <button class="order-btn save" onclick="saveOrder('${symbol}', '${type}', ${index})" disabled>Save</button>
      </td>
    `;
    return row;
  }

  // Create order row (legacy function for compatibility)
  function createOrderRow(order, symbol, type, index) {
    return createAccordionOrderRow(order, symbol, type, index);
  }

  // Edit order function
  window.editOrder = function (symbol, type, index) {
    console.log(`Edit order: ${symbol}, ${type}, ${index}`);
    // TODO: Implement edit functionality
  };

  // Close order function
  window.closeOrder = function (symbol, type, index) {
    console.log(`Close order: ${symbol}, ${type}, ${index}`);
    // TODO: Implement close functionality
  };

  // Save order function
  window.saveOrder = function (symbol, type, index) {
    console.log(`Save order: ${symbol}, ${type}, ${index}`);
    // TODO: Implement save functionality
  };
});

// Symbols modal functionality
document.addEventListener("DOMContentLoaded", function () {
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
  symbolsBtn.addEventListener("click", function () {
    symbolsModal.classList.add("show");
    loadSymbols();
  });

  // Close modal
  symbolsModalClose.addEventListener("click", function () {
    symbolsModal.classList.remove("show");
  });

  // Close modal when clicking outside
  symbolsModal.addEventListener("click", function (e) {
    if (e.target === symbolsModal) {
      symbolsModal.classList.remove("show");
    }
  });

  // Search functionality
  symbolsSearch.addEventListener("input", function () {
    const searchTerm = this.value.toLowerCase();
    filteredSymbols = allSymbols.filter((symbol) =>
      symbol.toLowerCase().includes(searchTerm)
    );
    renderSymbols();
  });

  // Load symbols from API data
  function loadSymbols() {
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
        totalSymbolsCount.textContent = allSymbols.length;
        renderSymbols();
      })
      .catch((error) => {
        console.error("Error loading symbols:", error);
        allSymbols = [];
        filteredSymbols = [];
        renderSymbols();
      });
  }

  // Render symbols list
  function renderSymbols() {
    symbolsList.innerHTML = "";
    filteredSymbols.forEach((symbol) => {
      const symbolItem = document.createElement("div");
      symbolItem.className = "symbol-item";
      if (selectedSymbols.has(symbol)) {
        symbolItem.classList.add("selected");
      }
      symbolItem.textContent = symbol.toUpperCase();
      symbolItem.addEventListener("click", function () {
        toggleSymbol(symbol);
      });
      symbolsList.appendChild(symbolItem);
    });
    updateSelectedCount();
  }

  // Toggle symbol selection
  function toggleSymbol(symbol) {
    if (selectedSymbols.has(symbol)) {
      selectedSymbols.delete(symbol);
    } else {
      selectedSymbols.add(symbol);
    }
    renderSymbols();
  }

  // Update selected count
  function updateSelectedCount() {
    selectedSymbolsCount.textContent = selectedSymbols.size;
  }
});

// Load tokens data
async function loadTokensData() {
  const loadingIndicator = document.getElementById("loadingIndicator");
  const tokensContainer = document.getElementById("tokensContainer");

  try {
    const response = await fetch("/api/data");
    const data = await response.json();

    if (data && Object.keys(data).length > 0) {
      renderTokensData(data);
      updateStats(data);
      updateCount();
    } else {
      const tokensTable = document.getElementById("tokensTable");
      const tokensContainer = document.getElementById("tokensContainer");
      tokensTable.style.display = "none";
      tokensContainer.style.display = "block";
      tokensContainer.innerHTML =
        '<div class="no-data"><h3>No token data available</h3><p>Make sure the tokens analyzer is running and generating data.</p></div>';
    }
  } catch (error) {
    console.error("Error loading tokens data:", error);
    const tokensTable = document.getElementById("tokensTable");
    const tokensContainer = document.getElementById("tokensContainer");
    tokensTable.style.display = "none";
    tokensContainer.style.display = "block";
    tokensContainer.innerHTML =
      '<div class="no-data"><h3>Error loading data</h3><p>Please try again.</p></div>';
  }
}

// Update count
function updateCount() {
  const updateCount = document.getElementById("updateCount");
  const current = parseInt(updateCount.textContent) || 0;
  updateCount.textContent = current + 1;
}

// Apply filters
async function applyFilters() {
  const periods = {
    delta: document.getElementById("deltaPeriod").value,
    vol: document.getElementById("volPeriod").value,
    trade: document.getElementById("tradePeriod").value,
    NATR: document.getElementById("natrPeriod").value,
    spread: document.getElementById("spreadPeriod").value,
    activity: document.getElementById("activityPeriod").value,
  };

  const thresholds = {
    delta: parseFloat(document.getElementById("deltaThreshold").value) || 0,
    vol: parseFloat(document.getElementById("volThreshold").value) || 0,
    trade: parseInt(document.getElementById("tradeThreshold").value) || 0,
    NATR: parseFloat(document.getElementById("natrThreshold").value) || 0,
    spread: parseFloat(document.getElementById("spreadThreshold").value) || 0,
    activity:
      parseFloat(document.getElementById("activityThreshold").value) || 0,
  };

  try {
    const response = await fetch("/api/update-filters", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ periods, thresholds }),
    });

    if (response.ok) {
      console.log("Filters applied successfully");
      loadTokensData();
    } else {
      console.error("Failed to apply filters");
    }
  } catch (error) {
    console.error("Error applying filters:", error);
  }
}

// Reset filters
function resetFilters() {
  document.getElementById("deltaPeriod").value = "1h";
  document.getElementById("volPeriod").value = "1h";
  document.getElementById("tradePeriod").value = "1h";
  document.getElementById("natrPeriod").value = "1h";
  document.getElementById("spreadPeriod").value = "1h";
  document.getElementById("activityPeriod").value = "1h";

  document.getElementById("deltaThreshold").value = "0";
  document.getElementById("volThreshold").value = "0";
  document.getElementById("tradeThreshold").value = "0";
  document.getElementById("natrThreshold").value = "0";
  document.getElementById("spreadThreshold").value = "0";
  document.getElementById("activityThreshold").value = "0";

  applyFilters();
}

// Render tokens data
function renderTokensData(data) {
  const tokensTable = document.getElementById("tokensTable");
  const tokensTableBody = document.getElementById("tokensTableBody");
  const tokensContainer = document.getElementById("tokensContainer");

  // Hide old container, show table
  tokensContainer.style.display = "none";
  tokensTable.style.display = "table";

  let html = "";

  for (const [exchange, tokens] of Object.entries(data)) {
    for (const [symbol, metrics] of Object.entries(tokens)) {
      html += `
        <tr>
          <td class="exchange-cell">${exchange.toUpperCase()}</td>
          <td class="symbol-cell">${symbol.toUpperCase()}</td>
          <td class="metric-cell">${metrics.delta.toFixed(4)}</td>
          <td class="metric-cell">${metrics.vol.toFixed(2)}</td>
          <td class="metric-cell">${metrics.trade}</td>
          <td class="metric-cell">${metrics.NATR.toFixed(4)}</td>
          <td class="metric-cell">${metrics.spread.toFixed(4)}</td>
          <td class="metric-cell">${metrics.activity.toFixed(2)}</td>
        </tr>
      `;
    }
  }

  tokensTableBody.innerHTML = html;
}

// Update stats
function updateStats(data) {
  const totalTokens = Object.values(data).reduce(
    (sum, tokens) => sum + Object.keys(tokens).length,
    0
  );
  const totalExchanges = Object.keys(data).length;

  document.getElementById("totalTokens").textContent = totalTokens;
  document.getElementById("totalExchanges").textContent = totalExchanges;
}

// Auto-refresh data every 1 second
setInterval(loadTokensData, 1000);

// Load data on page load
document.addEventListener("DOMContentLoaded", function () {
  loadTokensData();
});
