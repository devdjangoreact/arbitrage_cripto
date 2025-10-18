// Main Application Entry Point - Modular Architecture
document.addEventListener("DOMContentLoaded", async function () {
  console.log("🚀 Initializing modular application...");

  try {
    // Initialize core application
    await window.app.init();

    // Initialize all managers
    window.uiManager.init();
    window.ordersManager.setupOrdersFunctionality();
    window.symbolsManager.setupSymbolsModal();
    window.modalsManager.setupConfirmationModal();
    window.modalsManager.setupOrderModal();
    window.uiManager.setupFilterListeners();

    console.log("✅ All modules initialized successfully");

    // Setup global event handlers for charts and accordions
    setupGlobalEventHandlers();
  } catch (error) {
    console.error("❌ Failed to initialize application:", error);
  }
});

// Setup global event handlers for charts and accordions
function setupGlobalEventHandlers() {
  // Make functions globally available for onclick handlers in templates
  window.toggleChartSection = window.chartsManager.toggleChartSection.bind(
    window.chartsManager
  );
  window.toggleOrderBookSection =
    window.chartsManager.toggleOrderBookSection.bind(window.chartsManager);
  window.toggleAccordion = window.chartsManager.toggleAccordion.bind(
    window.chartsManager
  );
  window.manualRefresh = window.analyzerManager.manualRefresh.bind(
    window.analyzerManager
  );
  window.applyFilters = window.analyzerManager.applyFilters.bind(
    window.analyzerManager
  );
  window.resetFilters = window.analyzerManager.resetFilters.bind(
    window.analyzerManager
  );

  // Orders manager functions
  window.editOrder = window.ordersManager.editOrder.bind(window.ordersManager);
  window.saveOrder = window.ordersManager.saveOrder.bind(window.ordersManager);
  window.closeOrder = window.ordersManager.closeOrder.bind(
    window.ordersManager
  );
  window.cancelEdit = window.ordersManager.cancelEdit.bind(
    window.ordersManager
  );

  console.log("🔗 Global event handlers configured");
}
