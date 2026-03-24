// State
let tokensData = {};
let spreadRows = [];
let currentSort = { column: "spread", order: "desc" };
let currentFilters = {
  exchangePair: "all",
  minSpread: 0,
  tokenSearch: "",
};

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  initializeTabs();
  initializeButtons();
  initializeSortButtons();
  loadTokensData();
  updateTimestamp();
  setInterval(updateTimestamp, 1000);
  setInterval(loadTokensData, 30000); // Auto-refresh every 30 seconds
});

// Tab Management
function initializeTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tabName = btn.dataset.tab;
      switchTab(tabName);
    });
  });
}

function switchTab(tabName) {
  // Update tab buttons
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.remove("active");
    if (btn.dataset.tab === tabName) {
      btn.classList.add("active");
    }
  });

  // Update tab content
  document.querySelectorAll(".tab-content").forEach((content) => {
    content.classList.remove("active");
  });
  document.getElementById(`${tabName}-tab`).classList.add("active");

  // Load data for tab
  if (tabName === "tokens") {
    loadTokensData();
  } else if (tabName === "spread") {
    loadSpreadData();
  }
}

// Button Initialization
function initializeButtons() {
  document
    .getElementById("refresh-btn")
    .addEventListener("click", loadTokensData);
  document
    .getElementById("refresh-spread-btn")
    .addEventListener("click", loadSpreadData);
  document
    .getElementById("apply-filters-btn")
    .addEventListener("click", applyFilters);
  document
    .getElementById("exchange-filter")
    .addEventListener("change", filterTokensByExchange);

  // Spread filters
  document
    .getElementById("exchange-pair-filter")
    .addEventListener("change", (e) => {
      currentFilters.exchangePair = e.target.value;
      renderSpreadTable();
    });

  document
    .getElementById("min-spread-filter")
    .addEventListener("change", (e) => {
      currentFilters.minSpread = parseFloat(e.target.value);
      renderSpreadTable();
    });

  document.getElementById("token-search").addEventListener("input", (e) => {
    currentFilters.tokenSearch = e.target.value.toLowerCase();
    renderSpreadTable();
  });
}

// Sort Buttons
function initializeSortButtons() {
  document.querySelectorAll(".sort-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const column = btn.dataset.sort;
      const order = btn.dataset.order;

      // Update active state
      document
        .querySelectorAll(".sort-btn")
        .forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      // Update sort
      currentSort = { column, order };
      renderSpreadTable();
    });
  });
}

// API Functions
async function loadTokensData() {
  try {
    const response = await fetch("/api/data?t=" + Date.now());
    const data = await response.json();

    // Remove timestamp from data for processing
    const tokensDataRaw = { ...data };
    delete tokensDataRaw._timestamp;
    delete tokensDataRaw._error;

    tokensData = tokensDataRaw;

    // Process spread data
    processSpreadData(tokensData);

    renderTokensData(tokensData);
    updateExchangeFilter(tokensData);
    updateStatus("online");
  } catch (error) {
    console.error("Error loading tokens data:", error);
    document.getElementById("tokens-data").innerHTML = `
            <div class="error">Error loading data: ${error.message}</div>
        `;
    document.getElementById("spread-data").innerHTML = `
            <div class="error">Error loading data: ${error.message}</div>
        `;
    updateStatus("error");
  }
}

async function loadSpreadData() {
  // Data is already loaded via loadTokensData
  renderSpreadTable();
}

async function applyFilters() {
  const periods = {
    delta: document.getElementById("period-delta").value,
    vol: document.getElementById("period-vol").value,
    trade: document.getElementById("period-trade").value,
    natr: document.getElementById("period-natr").value,
    spread: document.getElementById("period-spread").value,
    activity: document.getElementById("period-activity").value,
  };

  const thresholds = {
    delta: parseFloat(document.getElementById("threshold-delta").value) || 0,
    vol: parseFloat(document.getElementById("threshold-vol").value) || 0,
    trade: parseFloat(document.getElementById("threshold-trade").value) || 0,
    natr: parseFloat(document.getElementById("threshold-natr").value) || 0,
    spread: parseFloat(document.getElementById("threshold-spread").value) || 0,
    activity:
      parseFloat(document.getElementById("threshold-activity").value) || 0,
  };

  try {
    const response = await fetch("/api/update-filters", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ periods, thresholds }),
    });
    const result = await response.json();

    if (result.status === "success") {
      showNotification("Filters applied successfully!", "success");
      loadTokensData();
    } else {
      showNotification("Error applying filters: " + result.message, "error");
    }
  } catch (error) {
    showNotification("Error applying filters: " + error.message, "error");
  }
}

// Process Spread Data
function processSpreadData(data) {
  spreadRows = [];

  // Handle empty or invalid data
  if (!data || typeof data !== "object") {
    console.warn("Invalid data received:", data);
    return;
  }

  // Group data by token across exchanges
  const tokenExchangeMap = {};

  for (const [exchange, tokens] of Object.entries(data)) {
    // Skip non-exchange keys (like _timestamp, _error)
    if (exchange.startsWith("_")) continue;

    if (!tokens || typeof tokens !== "object") continue;

    for (const [token, metrics] of Object.entries(tokens)) {
      if (!tokenExchangeMap[token]) {
        tokenExchangeMap[token] = {};
      }
      tokenExchangeMap[token][exchange] = {
        ...metrics,
        exchange,
      };
    }
  }

  // Create spread rows for each exchange pair
  for (const [token, exchanges] of Object.entries(tokenExchangeMap)) {
    const exchangeList = Object.keys(exchanges);

    // Need at least 2 exchanges for spread
    if (exchangeList.length < 2) continue;

    // Create pairs
    for (let i = 0; i < exchangeList.length; i++) {
      for (let j = i + 1; j < exchangeList.length; j++) {
        const ex1 = exchangeList[i];
        const ex2 = exchangeList[j];
        const metrics1 = exchanges[ex1];
        const metrics2 = exchanges[ex2];

        // Skip if metrics are invalid
        if (!metrics1 || !metrics2) continue;

        // Calculate spread (difference in delta)
        const spread = Math.abs((metrics1.delta || 0) - (metrics2.delta || 0));

        // Determine buy/sell exchanges based on delta
        const buyExchange =
          (metrics1.delta || 0) < (metrics2.delta || 0) ? ex1 : ex2;
        const sellExchange =
          (metrics1.delta || 0) < (metrics2.delta || 0) ? ex2 : ex1;
        const avgVolume = ((metrics1.vol || 0) + (metrics2.vol || 0)) / 2;

        spreadRows.push({
          token,
          exchange1: ex1,
          exchange2: ex2,
          buyExchange,
          sellExchange,
          spread,
          volume1: metrics1.vol || 0,
          volume2: metrics2.vol || 0,
          avgVolume,
          delta1: metrics1.delta,
          delta2: metrics2.delta,
          metrics1,
          metrics2,
        });
      }
    }
  }

  updateExchangePairFilter();
}

// Render Functions
function renderTokensData(data) {
  const container = document.getElementById("tokens-data");
  const exchangeFilter = document.getElementById("exchange-filter").value;

  let html = "";

  for (const [exchange, tokens] of Object.entries(data)) {
    if (exchangeFilter !== "all" && exchange !== exchangeFilter) continue;

    const tokenCount = Object.keys(tokens).length;
    if (tokenCount === 0) continue;

    html += `
            <div class="exchange-section">
                <h2 class="exchange-header">📈 ${exchange.toUpperCase()} (${tokenCount} tokens)</h2>
                <div class="tokens-grid">
        `;

    for (const [token, metrics] of Object.entries(tokens)) {
      html += `
                <div class="token-card">
                    <div class="token-name">${token}</div>
                    <div class="metrics-grid">
                        <div class="metric">
                            <div class="metric-label">Delta</div>
                            <div class="metric-value highlight">${(metrics.delta * 100).toFixed(4)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Volume</div>
                            <div class="metric-value">${formatNumber(metrics.vol)}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Trades</div>
                            <div class="metric-value">${metrics.trade}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">NATR</div>
                            <div class="metric-value">${(metrics.natr * 100).toFixed(4)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Spread</div>
                            <div class="metric-value">${(metrics.spread * 100).toFixed(4)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Activity</div>
                            <div class="metric-value">${metrics.activity.toFixed(2)}/s</div>
                        </div>
                    </div>
                </div>
            `;
    }

    html += `
                </div>
            </div>
        `;
  }

  if (!html) {
    html = '<div class="loading">No tokens data available</div>';
  }

  container.innerHTML = html;
}

function renderSpreadTable() {
  const container = document.getElementById("spread-data");

  // Apply filters
  let filteredRows = spreadRows.filter((row) => {
    // Exchange pair filter
    if (currentFilters.exchangePair !== "all") {
      const pair = [row.exchange1, row.exchange2].sort().join("-");
      if (pair !== currentFilters.exchangePair) return false;
    }

    // Min spread filter
    if (row.spread < currentFilters.minSpread) return false;

    // Token search filter
    if (
      currentFilters.tokenSearch &&
      !row.token.toLowerCase().includes(currentFilters.tokenSearch)
    ) {
      return false;
    }

    return true;
  });

  // Sort
  filteredRows.sort((a, b) => {
    let aVal, bVal;

    switch (currentSort.column) {
      case "spread":
        aVal = a.spread;
        bVal = b.spread;
        break;
      case "volume":
        aVal = a.avgVolume;
        bVal = b.avgVolume;
        break;
      case "token":
        aVal = a.token.toLowerCase();
        bVal = b.token.toLowerCase();
        break;
      default:
        aVal = a.spread;
        bVal = b.spread;
    }

    if (currentSort.order === "asc") {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });

  // Render stats
  const statsHtml = `
        <div class="stats-summary">
            <div class="stat-card">
                <div class="stat-value">${filteredRows.length}</div>
                <div class="stat-label">Opportunities</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${getMaxSpread(filteredRows)}</div>
                <div class="stat-label">Max Spread</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${getAvgSpread(filteredRows)}</div>
                <div class="stat-label">Avg Spread</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${formatNumber(getTotalVolume(filteredRows))}</div>
                <div class="stat-label">Total Volume</div>
            </div>
        </div>
    `;

  // Render table
  let html =
    statsHtml +
    `
        <div class="spread-table-container">
            <table class="spread-table">
                <thead>
                    <tr>
                        <th class="sortable" data-sort="token">Token</th>
                        <th>Exchange Pair</th>
                        <th class="sortable" data-sort="spread">Spread</th>
                        <th class="sortable" data-sort="volume">Avg Volume</th>
                        <th>Buy On</th>
                        <th>Sell On</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
    `;

  for (const row of filteredRows) {
    const spreadClass = getSpreadClass(row.spread);
    const isOpportunity = row.spread >= 0.01;

    html += `
            <tr class="${isOpportunity ? "arbitrage-opportunity" : ""}">
                <td class="token-cell">${row.token}</td>
                <td>
                    <div class="exchange-pair-cell">
                        <span class="exchange-badge">${row.exchange1}</span>
                        <span class="exchange-arrow">↔</span>
                        <span class="exchange-badge">${row.exchange2}</span>
                    </div>
                </td>
                <td class="spread-value ${spreadClass}">${(row.spread * 100).toFixed(4)}%</td>
                <td class="volume-cell">${formatNumber(row.avgVolume)}</td>
                <td>
                    <span class="exchange-badge" style="background: rgba(0, 255, 136, 0.2); color: #00ff88;">
                        ${row.buyExchange}
                    </span>
                </td>
                <td>
                    <span class="exchange-badge" style="background: rgba(255, 71, 87, 0.2); color: #ff4757;">
                        ${row.sellExchange}
                    </span>
                </td>
                <td>
                    <button class="action-btn action-btn-buy" onclick="showNotification('Buy on ${row.buyExchange}', 'success')">
                        Buy
                    </button>
                    <button class="action-btn action-btn-sell" onclick="showNotification('Sell on ${row.sellExchange}', 'error')">
                        Sell
                    </button>
                </td>
            </tr>
        `;
  }

  html += `
                </tbody>
            </table>
        </div>
    `;

  if (filteredRows.length === 0) {
    html =
      statsHtml +
      '<div class="loading">No spread data matches current filters</div>';
  }

  container.innerHTML = html;

  // Add sort indicators
  updateSortIndicators();
}

// Helper Functions
function getSpreadClass(spread) {
  if (spread >= 0.01) return "high";
  if (spread >= 0.005) return "medium";
  return "low";
}

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(2) + "M";
  if (num >= 1000) return (num / 1000).toFixed(2) + "K";
  return num.toFixed(2);
}

function updateExchangeFilter(data) {
  const select = document.getElementById("exchange-filter");
  const currentValue = select.value;
  const exchanges = Object.keys(data);

  select.innerHTML = '<option value="all">All Exchanges</option>';
  exchanges.forEach((exchange) => {
    select.innerHTML += `<option value="${exchange}">${exchange.toUpperCase()}</option>`;
  });

  select.value = currentValue;
}

function updateExchangePairFilter() {
  const select = document.getElementById("exchange-pair-filter");
  const currentValue = select.value;

  // Get unique exchange pairs
  const pairs = new Set();
  spreadRows.forEach((row) => {
    const pair = [row.exchange1, row.exchange2].sort().join("-");
    pairs.add(pair);
  });

  select.innerHTML = '<option value="all">All Exchange Pairs</option>';
  pairs.forEach((pair) => {
    select.innerHTML += `<option value="${pair}">${pair.replace("-", " ↔ ")}</option>`;
  });

  select.value = currentValue;
}

function filterTokensByExchange() {
  renderTokensData(tokensData);
}

function updateStatus(status) {
  const statusText = document.getElementById("status-text");
  const statusIndicator = document.querySelector(".status-indicator");

  if (status === "online") {
    statusText.textContent = "Online";
    statusIndicator.style.background = "#00ff88";
  } else if (status === "error") {
    statusText.textContent = "Error";
    statusIndicator.style.background = "#ff4757";
  } else {
    statusText.textContent = "Loading...";
    statusIndicator.style.background = "#ffa502";
  }
}

function updateTimestamp() {
  const now = new Date();
  document.getElementById("timestamp").textContent =
    "Last update: " + now.toLocaleString();
}

function showNotification(message, type) {
  // Remove existing notifications
  document.querySelectorAll(".notification").forEach((n) => n.remove());

  // Create notification element
  const notification = document.createElement("div");
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === "success" ? "#00ff88" : "#ff4757"};
        color: #1a1a2e;
        border-radius: 10px;
        font-weight: bold;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;

  document.body.appendChild(notification);

  // Remove after 3 seconds
  setTimeout(() => {
    notification.style.animation = "slideOut 0.3s ease";
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

function updateSortIndicators() {
  document.querySelectorAll(".sortable").forEach((th) => {
    th.classList.remove("sorted-asc", "sorted-desc");
    if (th.dataset.sort === currentSort.column) {
      th.classList.add(`sorted-${currentSort.order}`);
    }
  });
}

function getMaxSpread(rows) {
  if (rows.length === 0) return "0%";
  const max = Math.max(...rows.map((r) => r.spread));
  return (max * 100).toFixed(4) + "%";
}

function getAvgSpread(rows) {
  if (rows.length === 0) return "0%";
  const avg = rows.reduce((sum, r) => sum + r.spread, 0) / rows.length;
  return (avg * 100).toFixed(4) + "%";
}

function getTotalVolume(rows) {
  return rows.reduce((sum, r) => sum + r.avgVolume, 0);
}

// Add animation styles
const style = document.createElement("style");
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
