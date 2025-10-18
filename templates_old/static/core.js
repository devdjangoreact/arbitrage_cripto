// Core functionality and template system
class AppCore {
  constructor() {
    this.templates = {};
    this.symbolsData = [];
    this.exchangesData = [];
    this.ordersData = [];
    this.availableExchanges = [];
    this.availableSymbols = [];
  }

  // Initialize the application
  async init() {
    console.log("Initializing application...");

    // Load templates first
    await this.loadTemplates();

    // Then setup all functionality
    this.setupEventListeners();
    this.loadAvailableExchanges();
    this.loadAvailableSymbols();
    this.setupDataLoading();
  }

  // Load HTML templates
  async loadTemplates() {
    const templateFiles = [
      "templates/content/orders_accordion_item.html",
      "templates/content/tokens_accordion_item.html",
      "templates/content/order_details_modal.html",
    ];

    for (const file of templateFiles) {
      try {
        const response = await fetch(`/${file}`);
        if (response.ok) {
          this.templates[file] = await response.text();
        } else {
          console.error(`Failed to load template: ${file}`);
        }
      } catch (error) {
        console.error(`Error loading template ${file}:`, error);
      }
    }
    console.log("Templates loaded:", Object.keys(this.templates));
  }

  // Render template with data
  renderTemplate(templateName, data) {
    if (!this.templates[templateName]) {
      console.error(`Template not found: ${templateName}`);
      return "";
    }

    let html = this.templates[templateName];
    for (const [key, value] of Object.entries(data)) {
      const placeholder = `{{${key}}}`;
      html = html.replace(new RegExp(placeholder, "g"), value || "");
    }
    return html;
  }

  // Setup global event listeners
  setupEventListeners() {
    // Store current symbol context for templates
    window.currentSymbolContext = null;

    // Global error handler
    window.addEventListener("error", (e) => {
      console.error("Global error:", e.error);
    });

    // Global unhandled promise rejection handler
    window.addEventListener("unhandledrejection", (e) => {
      console.error("Unhandled promise rejection:", e.reason);
    });
  }

  // Load available exchanges from utils/exchange.json
  loadAvailableExchanges() {
    fetch("/utils/exchange.json")
      .then((response) => response.json())
      .then((data) => {
        this.availableExchanges = data
          .filter((ex) => ex.use)
          .map((ex) => ex.exchange);
        console.log("Available exchanges loaded:", this.availableExchanges);
      })
      .catch((error) => {
        console.error("Error loading exchanges:", error);
        // Fallback to hardcoded list
        this.availableExchanges = ["gate", "bitget", "bingx", "mexc"];
      });
  }

  // Load available symbols from utils/symbols.json
  loadAvailableSymbols() {
    fetch("/utils/symbols.json")
      .then((response) => response.json())
      .then((data) => {
        this.availableSymbols = data
          .filter((sym) => sym.use)
          .map((sym) => sym.symbol);
        console.log("Available symbols loaded:", this.availableSymbols);
        this.updateFilterOptions();
      })
      .catch((error) => {
        console.error("Error loading symbols:", error);
        // Fallback to hardcoded list
        this.availableSymbols = [
          "BTC/USDT",
          "ETH/USDT",
          "BTC/USDT:USDT",
          "ETH/USDT:USDT",
        ];
        this.updateFilterOptions();
      });
  }

  // Update filter options with available exchanges and symbols
  updateFilterOptions() {
    // Update exchange filter
    const exchangeFilter = document.getElementById("exchangeFilter");
    if (exchangeFilter) {
      // Clear existing options except "All Exchanges"
      while (exchangeFilter.children.length > 1) {
        exchangeFilter.removeChild(exchangeFilter.lastChild);
      }

      // Add available exchanges
      this.availableExchanges.forEach((exchange) => {
        const option = document.createElement("option");
        option.value = exchange;
        option.textContent = exchange.toUpperCase();
        exchangeFilter.appendChild(option);
      });
    }

    // Update form symbol select
    const newOrderSymbol = document.getElementById("newOrderSymbol");
    if (newOrderSymbol) {
      // Clear existing options except "Select Symbol"
      while (newOrderSymbol.children.length > 1) {
        newOrderSymbol.removeChild(newOrderSymbol.lastChild);
      }

      // Add available symbols
      this.availableSymbols.forEach((symbol) => {
        const option = document.createElement("option");
        option.value = symbol;
        option.textContent = symbol.toUpperCase();
        newOrderSymbol.appendChild(option);
      });
    }

    // Update form exchange select
    const newOrderExchange = document.getElementById("newOrderExchange");
    if (newOrderExchange) {
      // Clear existing options except "Select Exchange"
      while (newOrderExchange.children.length > 1) {
        newOrderExchange.removeChild(newOrderExchange.lastChild);
      }

      // Add available exchanges
      this.availableExchanges.forEach((exchange) => {
        const option = document.createElement("option");
        option.value = exchange;
        option.textContent = exchange.toUpperCase();
        newOrderExchange.appendChild(option);
      });
    }

    // Update modal exchange select
    const orderExchange = document.getElementById("orderExchange");
    if (orderExchange) {
      // Clear existing options except "Select Exchange"
      while (orderExchange.children.length > 1) {
        orderExchange.removeChild(orderExchange.lastChild);
      }

      // Add available exchanges
      this.availableExchanges.forEach((exchange) => {
        const option = document.createElement("option");
        option.value = exchange;
        option.textContent = exchange.toUpperCase();
        orderExchange.appendChild(option);
      });
    }

    console.log("Filter options updated");
  }

  // Load data on page load and setup auto-refresh
  setupDataLoading() {
    // Load initial data
    this.loadTokensData();

    // Auto-refresh data every 20 seconds
    setInterval(() => {
      this.loadTokensData();
    }, 20000);
  }

  // Load tokens data
  async loadTokensData() {
    console.log("loadTokensData called at:", new Date().toLocaleTimeString());
    const loadingIndicator = document.getElementById("loadingIndicator");
    const tokensContainer = document.getElementById("tokensContainer");

    try {
      const response = await fetch("/api/data");
      const data = await response.json();

      if (data && Object.keys(data).length > 0) {
        if (window.analyzerManager) {
          window.analyzerManager.renderTokensData(data);
        }
        this.updateStats(data);
        this.updateCount();
      } else {
        const tokensTable = document.getElementById("tokensTable");
        const tokensContainer = document.getElementById("tokensContainer");
        tokensTable.style.display = "none";
        tokensContainer.style.display = "block";
        window.analyzerManager.showNoDataMessage();
      }
    } catch (error) {
      console.error("Error loading tokens data:", error);
      const tokensTable = document.getElementById("tokensTable");
      const tokensContainer = document.getElementById("tokensContainer");
      tokensTable.style.display = "none";
      tokensContainer.style.display = "block";
      window.analyzerManager.showErrorMessage();
    }
  }

  // Update count
  updateCount() {
    const updateCount = document.getElementById("updateCount");
    const current = parseInt(updateCount.textContent) || 0;
    updateCount.textContent = current + 1;
  }

  // Apply filters
  async applyFilters() {
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
        this.loadTokensData();
      } else {
        console.error("Failed to apply filters");
      }
    } catch (error) {
      console.error("Error applying filters:", error);
    }
  }

  // Reset filters
  resetFilters() {
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

    this.applyFilters();
  }

  // Manual refresh function
  manualRefresh() {
    console.log("Manual refresh triggered");
    const refreshBtn = document.querySelector(".manual-refresh-btn");

    // Show loading state
    if (refreshBtn) {
      refreshBtn.classList.add("loading");
      refreshBtn.disabled = true;
    }

    // Load data
    this.loadTokensData().finally(() => {
      // Remove loading state
      if (refreshBtn) {
        refreshBtn.classList.remove("loading");
        refreshBtn.disabled = false;
      }
    });
  }

  // Get color for exchange
  getExchangeColor(exchange) {
    const colors = {
      binance: "#F3BA2F",
      mexc: "#1e5f99",
      kucoin: "#00AFBD",
      gate: "#0157FF",
      huobi: "#FF6B35",
      bybit: "#F7931E",
      okx: "#000000",
      bitget: "#F39C12",
      default: "#6c757d",
    };
    return colors[exchange.toLowerCase()] || colors.default;
  }

  // Update stats
  updateStats(data) {
    if (!data || typeof data !== "object") return;

    const totalTokens = Object.values(data).reduce(
      (sum, tokens) => sum + (Object.keys(tokens || {}).length || 0),
      0
    );
    const totalExchanges = Object.keys(data).length;

    const totalTokensEl = document.getElementById("totalTokens");
    const totalExchangesEl = document.getElementById("totalExchanges");

    if (totalTokensEl) totalTokensEl.textContent = totalTokens;
    if (totalExchangesEl) totalExchangesEl.textContent = totalExchanges;
  }

  // Render tokens data (this will be overridden by analyzer module)
  renderTokensData(data) {
    // This is a placeholder - will be implemented in analyzer module
    console.log(
      "Rendering tokens data:",
      Object.keys(data).length,
      "exchanges"
    );
  }
}

// Create global app instance
window.app = new AppCore();
