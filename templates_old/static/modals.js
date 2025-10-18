// Modal Management functionality
class ModalsManager {
  constructor() {}

  // Setup confirmation modal functionality
  setupConfirmationModal() {
    console.log("Setting up confirmation modal...");
    const confirmationModal = document.getElementById("confirmationModal");
    const confirmationModalClose = document.getElementById(
      "confirmationModalClose"
    );
    const confirmationCancelBtn = document.getElementById(
      "confirmationCancelBtn"
    );
    const confirmationConfirmBtn = document.getElementById(
      "confirmationConfirmBtn"
    );

    console.log("Modal elements found:", {
      modal: !!confirmationModal,
      close: !!confirmationModalClose,
      cancel: !!confirmationCancelBtn,
      confirm: !!confirmationConfirmBtn,
    });

    if (confirmationModalClose) {
      confirmationModalClose.addEventListener("click", function () {
        console.log("Close button clicked");
        confirmationModal.style.display = "none";
      });
    }

    if (confirmationCancelBtn) {
      confirmationCancelBtn.addEventListener("click", function () {
        console.log("Cancel button clicked");
        confirmationModal.style.display = "none";
      });
    }

    if (confirmationConfirmBtn) {
      confirmationConfirmBtn.addEventListener(
        "click",
        function () {
          console.log("Confirm button clicked");
          const operation = confirmationConfirmBtn.dataset.operation;
          const orderData = JSON.parse(
            confirmationConfirmBtn.dataset.orderData || "{}"
          );

          console.log("Operation:", operation, "Order data:", orderData);

          if (operation === "save") {
            this.performSaveOperation(orderData);
          } else if (operation === "close") {
            this.performCloseOperation(orderData);
          }

          confirmationModal.style.display = "none";
        }.bind(this)
      );
    }

    // Close modal when clicking outside
    if (confirmationModal) {
      confirmationModal.addEventListener("click", function (e) {
        if (e.target === confirmationModal) {
          confirmationModal.style.display = "none";
        }
      });
    }
  }

  // Setup order modal functionality
  setupOrderModal() {
    console.log("Setting up order modal...");
    const orderModal = document.getElementById("orderModal");
    const orderModalClose = document.getElementById("orderModalClose");
    const cancelOrderBtn = document.getElementById("cancelOrderBtn");
    const saveOrderBtn = document.getElementById("saveOrderBtn");

    console.log("Order modal elements found:", {
      modal: !!orderModal,
      close: !!orderModalClose,
      cancel: !!cancelOrderBtn,
      save: !!saveOrderBtn,
    });

    if (orderModalClose) {
      orderModalClose.addEventListener("click", function () {
        console.log("Order modal close button clicked");
        orderModal.style.display = "none";
      });
    }

    if (cancelOrderBtn) {
      cancelOrderBtn.addEventListener("click", function () {
        console.log("Order modal cancel button clicked");
        orderModal.style.display = "none";
      });
    }

    if (saveOrderBtn) {
      saveOrderBtn.addEventListener("click", function (e) {
        e.preventDefault();
        // Handle order form submission
        console.log("Order form submitted");
        orderModal.style.display = "none";
      });
    }

    // Close modal when clicking outside
    if (orderModal) {
      orderModal.addEventListener("click", function (e) {
        if (e.target === orderModal) {
          orderModal.style.display = "none";
        }
      });
    }
  }

  // Perform save operation
  performSaveOperation(orderData) {
    console.log("Performing save operation for:", orderData);

    // Validate required fields before saving
    if (
      !orderData.symbol ||
      !orderData.exchange ||
      !orderData.side ||
      !orderData.type
    ) {
      console.error("Invalid order data - missing required fields:", orderData);
      alert("Error: Missing required order fields");
      return;
    }

    // Update or add the order in the data
    let orderUpdated = false;
    for (let symbolData of window.ordersManager.ordersData) {
      if (symbolData.symbol === orderData.symbol) {
        // Determine where to update/add based on order type
        if (orderData.type === "market" && symbolData.active?.positions) {
          // Update in positions for market orders
          const positionIndex = symbolData.active.positions.findIndex(
            (p) => p.id === orderData.id
          );
          if (positionIndex !== -1) {
            const oldOrder = symbolData.active.positions[positionIndex];
            symbolData.active.positions[positionIndex] = { ...orderData };
            console.log(
              `Updated market order in positions at index ${positionIndex}`,
              { old: oldOrder, new: orderData }
            );
            orderUpdated = true;
          } else {
            // Add new market order to positions
            symbolData.active.positions.push({ ...orderData });
            console.log(
              `Added new market order to positions for symbol ${orderData.symbol}`,
              orderData
            );
            orderUpdated = true;
          }
        } else if (orderData.type === "limit" && symbolData.active?.orders) {
          // Update in orders for limit orders
          const orderIndex = symbolData.active.orders.findIndex(
            (o) => o.id === orderData.id
          );
          if (orderIndex !== -1) {
            const oldOrder = symbolData.active.orders[orderIndex];
            symbolData.active.orders[orderIndex] = { ...orderData };
            console.log(
              `Updated limit order in orders at index ${orderIndex}`,
              {
                old: oldOrder,
                new: orderData,
              }
            );
            orderUpdated = true;
          } else {
            // Add new limit order to orders
            symbolData.active.orders.push({ ...orderData });
            console.log(
              `Added new limit order to orders for symbol ${orderData.symbol}`,
              orderData
            );
            orderUpdated = true;
          }
        } else {
          console.error(
            `No appropriate array found for order type ${orderData.type}`
          );
        }
        break;
      }
    }

    // If symbol doesn't exist in ordersData, create it
    if (!orderUpdated) {
      const newSymbolData = {
        symbol: orderData.symbol,
        active: {},
      };

      if (orderData.type === "market") {
        newSymbolData.active.positions = [{ ...orderData }];
        console.log(
          `Created new symbol entry and added market order to positions`,
          newSymbolData
        );
      } else if (orderData.type === "limit") {
        newSymbolData.active.orders = [{ ...orderData }];
        console.log(
          `Created new symbol entry and added limit order to orders`,
          newSymbolData
        );
      }

      window.ordersManager.ordersData.push(newSymbolData);
    }

    // Save to server
    fetch("/api/orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ orders: window.ordersManager.ordersData }),
    })
      .then((response) => response.json())
      .then((result) => {
        if (result.status === "success") {
          console.log("Order saved successfully, reloading data...");
          // Reload data to ensure consistency
          window.ordersManager.loadOrdersData();
        } else {
          alert("Error saving order: " + result.message);
        }
      })
      .catch((error) => {
        console.error("Error saving order:", error);
        alert("Error saving order");
      });
  }

  // Perform close operation
  performCloseOperation(orderData) {
    console.log("Performing close operation for:", orderData);

    // Move order from active to closed
    for (let symbolData of window.ordersManager.ordersData) {
      if (symbolData.symbol === orderData.symbol) {
        // Remove from appropriate array based on order type
        if (orderData.type === "market" && symbolData.active?.positions) {
          // Remove from positions for market orders
          symbolData.active.positions = symbolData.active.positions.filter(
            (p) => p.id !== orderData.id
          );
          console.log(
            `Removed market order from positions for ${orderData.symbol}`
          );
        } else if (orderData.type === "limit" && symbolData.active?.orders) {
          // Remove from orders for limit orders
          symbolData.active.orders = symbolData.active.orders.filter(
            (o) => o.id !== orderData.id
          );
          console.log(
            `Removed limit order from orders for ${orderData.symbol}`
          );
        }

        // Add to closed
        if (!symbolData.closed) symbolData.closed = [];
        orderData.close_date = new Date()
          .toISOString()
          .slice(0, 19)
          .replace("T", " ");
        symbolData.closed.push(orderData);
        console.log(`Added order to closed for ${orderData.symbol}`);
        break;
      }
    }

    // Save to server
    fetch("/api/orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ orders: window.ordersManager.ordersData }),
    })
      .then((response) => response.json())
      .then((result) => {
        if (result.status === "success") {
          window.ordersManager.renderOrdersTable();
        } else {
          alert("Error closing order: " + result.message);
        }
      })
      .catch((error) => {
        console.error("Error closing order:", error);
        alert("Error closing order");
      });
  }
}

// Create global modals manager instance
window.modalsManager = new ModalsManager();
