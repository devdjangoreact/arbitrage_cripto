// UI Management - Panel and Navigation functionality
class UIManager {
  constructor() {
    this.sidebar = null;
    this.rightSidePanel = null;
    this.pairsPanel = null;
    this.exchangesPanel = null;
    this.ordersSection = null;
    this.analyzerSection = null;
    this.dashboardSection = null;
    this.arbitrageSection = null;
    this.settingsSection = null;
    this.exchangesSection = null;
    this.logsSection = null;

    this.pairsTableBody = null;
    this.exchangesTableBody = null;

    this.menuToggle = null;
    this.pairsToggle = null;
    this.exchangesToggle = null;
    this.ordersToggle = null;
    this.analyzerToggle = null;
  }

  // Initialize UI elements and event listeners
  init() {
    this.getElements();
    this.setupPanelManagement();
    this.setupSidebarFunctionality();
  }

  // Get all DOM elements
  getElements() {
    this.menuToggle = document.getElementById("menuToggle");
    this.pairsToggle = document.getElementById("pairsToggle");
    this.exchangesToggle = document.getElementById("exchangesToggle");
    this.ordersToggle = document.getElementById("ordersToggle");
    this.analyzerToggle = document.getElementById("analyzerToggle");

    this.sidebar = document.getElementById("sidebar");
    this.rightSidePanel = document.getElementById("rightSidePanel");
    this.pairsPanel = document.getElementById("pairsPanel");
    this.exchangesPanel = document.getElementById("exchangesPanel");
    this.ordersSection = document.getElementById("ordersSection");
    this.analyzerSection = document.getElementById("analyzerSection");
    this.dashboardSection = document.getElementById("dashboardSection");
    this.arbitrageSection = document.getElementById("arbitrageSection");
    this.settingsSection = document.getElementById("settingsSection");
    this.exchangesSection = document.getElementById("exchangesSection");
    this.logsSection = document.getElementById("logsSection");

    this.pairsTableBody = document.getElementById("pairsTableBody");
    this.exchangesTableBody = document.getElementById("exchangesTableBody");
  }

  // Setup panel management functionality
  setupPanelManagement() {
    // Sidebar toggle - only collapse/expand sidebar
    if (this.menuToggle) {
      this.menuToggle.addEventListener("click", () => {
        this.sidebar.classList.toggle("collapsed");
      });
    }

    // Pairs panel toggle
    if (this.pairsToggle) {
      this.pairsToggle.addEventListener("click", () => {
        if (
          this.rightSidePanel.classList.contains("show") &&
          this.pairsPanel.classList.contains("show")
        ) {
          // If right panel is open and showing pairs, close it
          this.toggleRightSidePanel();
        } else if (
          this.rightSidePanel.classList.contains("show") &&
          this.exchangesPanel.classList.contains("show")
        ) {
          // If right panel is open but showing exchanges, switch to pairs
          this.exchangesPanel.classList.remove("show");
          this.exchangesToggle.classList.remove("active");
          this.pairsPanel.classList.add("show");
          this.pairsToggle.classList.add("active");
          if (window.symbolsManager) window.symbolsManager.loadSymbolsData();
        } else {
          // Open right panel with pairs
          this.rightSidePanel.classList.add("show");
          this.rightSidePanel.classList.remove("collapsed");
          this.exchangesPanel.classList.remove("show");
          this.exchangesToggle.classList.remove("active");
          this.pairsPanel.classList.add("show");
          this.pairsToggle.classList.add("active");
          if (window.symbolsManager) window.symbolsManager.loadSymbolsData();
        }
      });
    }

    // Exchanges panel toggle
    if (this.exchangesToggle) {
      this.exchangesToggle.addEventListener("click", () => {
        if (
          this.rightSidePanel.classList.contains("show") &&
          this.exchangesPanel.classList.contains("show")
        ) {
          // If right panel is open and showing exchanges, close it
          this.toggleRightSidePanel();
        } else if (
          this.rightSidePanel.classList.contains("show") &&
          this.pairsPanel.classList.contains("show")
        ) {
          // If right panel is open but showing pairs, switch to exchanges
          this.pairsPanel.classList.remove("show");
          this.pairsToggle.classList.remove("active");
          this.exchangesPanel.classList.add("show");
          this.exchangesToggle.classList.add("active");
          if (window.symbolsManager) window.symbolsManager.loadExchangesData();
        } else {
          // Open right panel with exchanges
          this.rightSidePanel.classList.add("show");
          this.rightSidePanel.classList.remove("collapsed");
          this.pairsPanel.classList.remove("show");
          this.pairsToggle.classList.remove("active");
          this.exchangesPanel.classList.add("show");
          this.exchangesToggle.classList.add("active");
          if (window.symbolsManager) window.symbolsManager.loadExchangesData();
        }
      });
    }

    // Orders section toggle
    if (this.ordersToggle) {
      this.ordersToggle.addEventListener("click", () => {
        if (this.ordersSection.style.display === "block") {
          this.ordersSection.style.display = "none";
          this.ordersToggle.classList.remove("active");
        } else {
          this.showMainSection(this.ordersSection, this.ordersToggle);
          if (window.ordersManager) window.ordersManager.loadOrdersData();
        }
      });
    }

    // Analyzer section toggle
    if (this.analyzerToggle) {
      this.analyzerToggle.addEventListener("click", () => {
        if (this.analyzerSection.style.display === "block") {
          this.analyzerSection.style.display = "none";
          this.analyzerToggle.classList.remove("active");
        } else {
          this.showMainSection(this.analyzerSection, this.analyzerToggle);
          if (window.analyzerManager) {
            window.analyzerManager.loadTokensData();
          }
        }
      });
    }
  }

  // Toggle right side panel
  toggleRightSidePanel() {
    if (this.rightSidePanel.classList.contains("show")) {
      this.rightSidePanel.classList.remove("show");
      this.rightSidePanel.classList.add("collapsed");
      this.pairsPanel.classList.remove("show");
      this.exchangesPanel.classList.remove("show");
      this.pairsToggle.classList.remove("active");
      this.exchangesToggle.classList.remove("active");
    } else {
      this.rightSidePanel.classList.add("show");
      this.rightSidePanel.classList.remove("collapsed");
    }
  }

  // Show main content section (Orders, Analyzer) - sidebar stays open
  showMainSection(section, toggle) {
    this.rightSidePanel.classList.remove("show");
    this.rightSidePanel.classList.add("collapsed");
    this.pairsPanel.classList.remove("show");
    this.exchangesPanel.classList.remove("show");
    this.ordersSection.style.display = "none";
    this.analyzerSection.style.display = "none";
    this.pairsToggle.classList.remove("active");
    this.exchangesToggle.classList.remove("active");
    this.ordersToggle.classList.remove("active");
    this.analyzerToggle.classList.remove("active");

    if (section) {
      section.style.display = "block";
    }
    toggle.classList.add("active");
  }

  // Show sidebar section
  showSidebarSection(section) {
    // Hide all sections
    this.dashboardSection.style.display = "none";
    this.analyzerSection.style.display = "none";
    this.arbitrageSection.style.display = "none";
    this.settingsSection.style.display = "none";
    this.exchangesSection.style.display = "none";
    this.logsSection.style.display = "none";
    this.ordersSection.style.display = "none";

    // Hide right panels
    this.rightSidePanel.classList.remove("show");
    this.rightSidePanel.classList.add("collapsed");
    this.pairsPanel.classList.remove("show");
    this.exchangesPanel.classList.remove("show");

    // Remove active states from all toggles
    this.pairsToggle.classList.remove("active");
    this.exchangesToggle.classList.remove("active");
    this.ordersToggle.classList.remove("active");
    this.analyzerToggle.classList.remove("active");

    // Show selected section
    if (section) {
      section.style.display = "block";
    }
  }

  // Hide sidebar and other panels, show specific panel
  showPanel(panel, toggle) {
    this.sidebar.classList.add("collapsed");
    this.pairsPanel.classList.remove("show");
    this.exchangesPanel.classList.remove("show");
    this.ordersSection.style.display = "none";
    this.analyzerSection.style.display = "none";
    this.pairsToggle.classList.remove("active");
    this.exchangesToggle.classList.remove("active");
    this.ordersToggle.classList.remove("active");
    this.analyzerToggle.classList.remove("active");

    if (panel) {
      panel.classList.add("show");
    } else if (toggle === this.ordersToggle) {
      this.ordersSection.style.display = "block";
    } else if (toggle === this.analyzerToggle) {
      this.analyzerSection.style.display = "block";
    }
    toggle.classList.add("active");
  }

  // Hide all panels and show sidebar
  showSidebar() {
    this.sidebar.classList.remove("collapsed");
    this.rightSidePanel.classList.remove("show");
    this.rightSidePanel.classList.add("collapsed");
    this.pairsPanel.classList.remove("show");
    this.exchangesPanel.classList.remove("show");
    this.ordersSection.style.display = "none";
    this.analyzerSection.style.display = "none";
    this.pairsToggle.classList.remove("active");
    this.exchangesToggle.classList.remove("active");
    this.ordersToggle.classList.remove("active");
    this.analyzerToggle.classList.remove("active");
  }

  // Setup sidebar functionality
  setupSidebarFunctionality() {
    // Dashboard
    const dashboardLink = document.querySelector('a[href="#"]:first-of-type');
    if (dashboardLink) {
      dashboardLink.addEventListener("click", (e) => {
        e.preventDefault();
        this.showSidebarSection(this.dashboardSection);
        // Update active state
        document
          .querySelectorAll(".sidebar-menu a")
          .forEach((link) => link.classList.remove("active"));
        dashboardLink.classList.add("active");
      });
    }

    // Analyzer
    const analyzerLink = document.querySelectorAll(".sidebar-menu a")[1];
    if (analyzerLink) {
      analyzerLink.addEventListener("click", (e) => {
        e.preventDefault();
        this.showSidebarSection(this.analyzerSection);
        // Update active state
        document
          .querySelectorAll(".sidebar-menu a")
          .forEach((link) => link.classList.remove("active"));
        analyzerLink.classList.add("active");
      });
    }

    // Arbitrage
    const arbitrageLink = document.querySelectorAll(".sidebar-menu a")[2];
    if (arbitrageLink) {
      arbitrageLink.addEventListener("click", (e) => {
        e.preventDefault();
        this.showSidebarSection(this.arbitrageSection);
        // Update active state
        document
          .querySelectorAll(".sidebar-menu a")
          .forEach((link) => link.classList.remove("active"));
        arbitrageLink.classList.add("active");
      });
    }

    // Exchanges
    const exchangesLink = document.querySelectorAll(".sidebar-menu a")[3];
    if (exchangesLink) {
      exchangesLink.addEventListener("click", (e) => {
        e.preventDefault();
        this.showSidebarSection(this.exchangesSection);
        // Update active state
        document
          .querySelectorAll(".sidebar-menu a")
          .forEach((link) => link.classList.remove("active"));
        exchangesLink.classList.add("active");
      });
    }

    // Settings
    const settingsLink = document.querySelectorAll(".sidebar-menu a")[4];
    if (settingsLink) {
      settingsLink.addEventListener("click", (e) => {
        e.preventDefault();
        this.showSidebarSection(this.settingsSection);
        // Update active state
        document
          .querySelectorAll(".sidebar-menu a")
          .forEach((link) => link.classList.remove("active"));
        settingsLink.classList.add("active");
      });
    }

    // Logs
    const logsLink = document.querySelectorAll(".sidebar-menu a")[5];
    if (logsLink) {
      logsLink.addEventListener("click", (e) => {
        e.preventDefault();
        this.showSidebarSection(this.logsSection);
        // Update active state
        document
          .querySelectorAll(".sidebar-menu a")
          .forEach((link) => link.classList.remove("active"));
        logsLink.classList.add("active");
      });
    }
  }

  // Setup filter listeners
  setupFilterListeners() {
    const filterInputs = document.querySelectorAll(
      "#dateFrom, #dateTo, #exchangeFilter, #pairFilter, #onlyActiveFilter"
    );
    filterInputs.forEach((input) => {
      if (input) {
        input.addEventListener("change", () => {
          console.log("Filter changed, refreshing orders table");
          if (window.ordersManager) window.ordersManager.renderOrdersTable();
        });
        input.addEventListener("input", () => {
          console.log("Filter input changed, refreshing orders table");
          if (window.ordersManager) window.ordersManager.renderOrdersTable();
        });
      }
    });
  }
}

// Create global UI manager instance
window.uiManager = new UIManager();
