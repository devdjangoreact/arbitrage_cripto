// Orders Management functionality
class OrdersManager {
  constructor() {
    this.ordersData = [];
  }

  // Setup orders functionality
  setupOrdersFunctionality() {
    console.log("Setting up orders functionality...");

    // Check if buttons exist
    const addOrderBtn = document.getElementById("addOrderBtn");
    const applyFiltersBtn = document.getElementById("applyFiltersBtn");
    const clearFiltersBtn = document.getElementById("clearFiltersBtn");

    console.log("Orders buttons found:", {
      addOrder: !!addOrderBtn,
      applyFilters: !!applyFiltersBtn,
      clearFilters: !!clearFiltersBtn,
    });

    // Use event delegation for dynamically loaded content
    document.addEventListener("click", (e) => {
      // Add Order button
      if (e.target && e.target.id === "addOrderBtn") {
        e.preventDefault();
        console.log("Add Order button clicked");
        const addOrderForm = document.getElementById("addOrderForm");
        if (addOrderForm) {
          addOrderForm.style.display =
            addOrderForm.style.display === "none" ? "block" : "none";
          if (addOrderForm.style.display === "block") {
            this.clearNewOrderForm();
            // Update form options when showing the form
            window.app.updateFilterOptions();
          }
        }
      }

      // Save New Order button
      if (e.target && e.target.id === "saveNewOrderBtn") {
        e.preventDefault();
        console.log("Save New Order button clicked");
        this.saveNewOrder();
      }

      // Delete New Order button
      if (e.target && e.target.id === "deleteNewOrderBtn") {
        e.preventDefault();
        console.log("Delete New Order button clicked");
        const addOrderForm = document.getElementById("addOrderForm");
        if (addOrderForm) {
          addOrderForm.style.display = "none";
          this.clearNewOrderForm();
        }
      }

      // Apply Filters button
      if (e.target && e.target.id === "applyFiltersBtn") {
        e.preventDefault();
        console.log("Apply Filters button clicked");
        this.renderOrdersTable();
      }

      // Clear Filters button
      if (e.target && e.target.id === "clearFiltersBtn") {
        e.preventDefault();
        console.log("Clear Filters button clicked");
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
        this.renderOrdersTable();
      }
    });
  }

  // Helper functions for orders functionality
  clearNewOrderForm() {
    const form = document.getElementById("addOrderForm");
    if (form) {
      const inputs = form.querySelectorAll("input, select");
      inputs.forEach((input) => {
        if (input.type === "number") {
          input.value =
            input.id === "newOrderLeverage"
              ? "1"
              : input.id === "newOrderFee"
              ? "0.001"
              : "";
        } else {
          input.value = "";
        }
      });
    }
  }

  // Load orders data
  loadOrdersData() {
    fetch("/api/orders")
      .then((response) => response.json())
      .then((result) => {
        if (result.status === "success") {
          this.ordersData = result.data;
          this.renderOrdersTable();
        } else {
          console.error("Error loading orders:", result.message);
        }
      })
      .catch((error) => {
        console.error("Error loading orders:", error);
      });
  }

  // Render orders accordion
  renderOrdersTable() {
    const accordion = document.getElementById("ordersAccordion");
    accordion.innerHTML = "";

    // Get filter values
    const dateFrom = document.getElementById("dateFrom")?.value;
    const dateTo = document.getElementById("dateTo")?.value;
    const exchangeFilter = document.getElementById("exchangeFilter")?.value;
    const pairFilter = document.getElementById("pairFilter")?.value;
    const onlyActive = document.getElementById("onlyActiveFilter")?.checked;

    this.ordersData.forEach((symbolData) => {
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

      // Create accordion item using template
      const templateData = {
        symbol: symbol,
        ordersCount: ordersCount,
        positionsCount: positionsCount,
        closedCount: closedCount
      };

      const accordionItemHTML = window.app.renderTemplate('templates/content/orders_accordion_item.html', templateData);
      const accordionItem = document.createElement("div");
      accordionItem.className = "accordion-item";
      accordionItem.innerHTML = accordionItemHTML;

      accordion.appendChild(accordionItem);

      // Add event listeners
      const header = accordionItem.querySelector(".accordion-header");
      const content = accordionItem.querySelector(".accordion-content");

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
          // Load all groups
          this.loadOrdersGroups(symbol);
        }
      }.bind(this));
    }.bind(this));
  }

  // Load orders groups content
  loadOrdersGroups(symbol) {
    const symbolData = this.ordersData.find((data) => data.symbol === symbol);
    if (!symbolData) return;

    // Get filter values
    const dateFrom = document.getElementById("dateFrom")?.value;
    const dateTo = document.getElementById("dateTo")?.value;
    const exchangeFilter = document.getElementById("exchangeFilter")?.value;

    // Load orders
    this.loadOrdersGroup(
      symbol,
      "orders",
      symbolData.active?.orders || [],
      dateFrom,
      dateTo,
      exchangeFilter
    );
    // Load positions
    this.loadOrdersGroup(
      symbol,
      "positions",
      symbolData.active?.positions || [],
      dateFrom,
      dateTo,
      exchangeFilter
    );
    // Load closed
    this.loadOrdersGroup(
      symbol,
      "closed",
      symbolData.closed || [],
      dateFrom,
      dateTo,
      exchangeFilter
    );
  }

  // Load specific orders group
  loadOrdersGroup(symbol, type, items, dateFrom, dateTo, exchangeFilter) {
    const tbody = document.querySelector(
      `.orders-tbody[data-symbol="${symbol}"][data-type="${type}"]`
    );
    if (!tbody) return;

    tbody.innerHTML = "";

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

      const row = this.createOrderRow(item, symbol, type, index);
      tbody.appendChild(row);
    });
  }

  // Create order row
  createOrderRow(order, symbol, type, index) {
    const row = document.createElement("tr");
    row.dataset.orderId = order.id;
    row.dataset.symbol = symbol;
    row.dataset.type = type;
    row.dataset.index = index;

    // Format date
    const orderDate = order.date
      ? new Date(order.date).toLocaleDateString()
      : "-";

    const closeDate = order.close_date
      ? new Date(order.close_date).toLocaleDateString()
      : "-";

    // Different row structure for closed orders
    if (type === "closed") {
      row.innerHTML = `
        <td class="order-date">${orderDate}</td>
        <td class="order-date">${closeDate}</td>
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
      `;
    } else {
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
          <button class="order-btn edit" onclick="window.ordersManager.editOrder('${symbol}', '${type}', ${index})">Edit</button>
          <button class="order-btn close" onclick="window.ordersManager.closeOrder('${symbol}', '${type}', ${index})">Close</button>
          <button class="order-btn save" onclick="window.ordersManager.saveOrder('${symbol}', '${type}', ${index})" disabled>Save</button>
        </td>
      `;
    }
    return row;
  }

  // Edit order function
  editOrder(symbol, type, index) {
    const symbolData = this.ordersData.find((data) => data.symbol === symbol);
    if (!symbolData) return;

    let order;
    console.log(
      `Looking for order: symbol=${symbol}, type=${type}, index=${index}`
    );
    console.log("Available data:", {
      ordersCount: symbolData.active?.orders?.length || 0,
      positionsCount: symbolData.active?.positions?.length || 0,
    });

    if (type === "orders" && symbolData.active?.orders) {
      if (symbolData.active.orders[index]) {
        order = symbolData.active.orders[index];
        console.log(`Found order in orders array at index ${index}:`, order);
      } else {
        console.error(
          `Order not found in orders at index ${index}. Available:`,
          symbolData.active.orders
        );
      }
    } else if (type === "positions" && symbolData.active?.positions) {
      if (symbolData.active.positions[index]) {
        order = symbolData.active.positions[index];
        console.log(`Found order in positions array at index ${index}:`, order);
      } else {
        console.error(
          `Order not found in positions at index ${index}. Available:`,
          symbolData.active.positions
        );
      }
    }

    if (!order) {
      console.error(
        `Order not found for symbol ${symbol}, type ${type}, index ${index}`
      );
      return;
    }

    console.log("Editing order:", order);

    // Make row editable
    const row = document.querySelector(
      `tr[data-symbol="${symbol}"][data-type="${type}"][data-index="${index}"]`
    );
    if (!row) return;

    // Enable editing for all cells except actions
    const cells = row.querySelectorAll("td:not(.order-actions)");
    cells.forEach((cell, cellIndex) => {
      if (cellIndex === 0) return; // Skip date column

      const fieldName = this.getFieldNameByIndex(cellIndex);
      if (!fieldName) return;

      cell.innerHTML = "";
      cell.className = "edit-cell";

      if (fieldName === "exchange") {
        // Create select for exchange
        const select = document.createElement("select");
        select.className = "edit-input";

        // Add options
        window.app.availableExchanges.forEach((ex) => {
          const option = document.createElement("option");
          option.value = ex;
          option.textContent = ex.toUpperCase();
          if (ex === order.exchange) {
            option.selected = true;
          }
          select.appendChild(option);
        });

        cell.appendChild(select);
      } else if (fieldName === "side") {
        // Create select for side
        const select = document.createElement("select");
        select.className = "edit-input";

        ["long", "short"].forEach((side) => {
          const option = document.createElement("option");
          option.value = side;
          option.textContent = side.toUpperCase();
          if (side === order.side) {
            option.selected = true;
          }
          select.appendChild(option);
        });

        cell.appendChild(select);
      } else if (fieldName === "type") {
        // Create select for type
        const select = document.createElement("select");
        select.className = "edit-input";

        ["market", "limit"].forEach((typeOption) => {
          const option = document.createElement("option");
          option.value = typeOption;
          option.textContent = typeOption.toUpperCase();
          if (typeOption === order.type) {
            option.selected = true;
          }
          select.appendChild(option);
        });

        cell.appendChild(select);
      } else {
        // Create text input for other fields
        const input = document.createElement("input");
        input.type = "text";
        input.className = "edit-input";
        input.value = order[fieldName] || "";
        cell.appendChild(input);
      }
    });

    // Update action buttons
    const actionsCell = row.querySelector(".order-actions");
    if (actionsCell) {
      actionsCell.innerHTML = `
        <button class="order-btn save" onclick="window.ordersManager.saveOrder('${symbol}', '${type}', ${index})">Save</button>
        <button class="order-btn cancel" onclick="window.ordersManager.cancelEdit('${symbol}', '${type}', ${index})">Cancel</button>
      `;
    }
  }

  // Helper function to map cell index to field name
  getFieldNameByIndex(cellIndex) {
    const fieldMap = [
      "date", // 0 - date (skip)
      "exchange", // 1 - exchange
      "side", // 2 - side
      "type", // 3 - type
      "price", // 4 - price
      "amount", // 5 - amount
      "leverage", // 6 - leverage
      "stop_loss", // 7 - stop_loss
      "take_profit", // 8 - take_profit
    ];
    console.log(
      `Mapping cell index ${cellIndex} to field: ${fieldMap[cellIndex]}`
    );
    return fieldMap[cellIndex] || null;
  }

  // Cancel edit function
  cancelEdit(symbol, type, index) {
    // Reload the row to restore original values
    this.loadOrdersGroups(symbol);
  }

  // Save order function
  saveOrder(symbol, type, index) {
    const symbolData = this.ordersData.find((data) => data.symbol === symbol);
    if (!symbolData) return;

    let order;
    if (type === "orders" && symbolData.active?.orders) {
      order = symbolData.active.orders[index];
      console.log(`Found order in orders array at index ${index}:`, order);
    } else if (type === "positions" && symbolData.active?.positions) {
      order = symbolData.active.positions[index];
      console.log(`Found order in positions array at index ${index}:`, order);
    }

    if (!order) {
      console.error(
        `Order not found for symbol ${symbol}, type ${type}, index ${index}`
      );
      return;
    }

    // Get updated values from form inputs
    const row = document.querySelector(
      `tr[data-symbol="${symbol}"][data-type="${type}"][data-index="${index}"]`
    );
    if (!row) return;

    const inputs = row.querySelectorAll(".edit-input");
    if (inputs.length === 0) {
      // No form inputs - use original order data for confirmation
      console.log("No form inputs found, using original order data:", order);
      this.showConfirmationModal(
        "save",
        order,
        `Are you sure you want to save changes to this ${type.slice(0, -1)}?`
      );
      return;
    }

    // Update order data from inputs/selects
    const updatedOrder = { ...order };
    const fieldMap = [
      "date",
      "exchange",
      "side",
      "type",
      "price",
      "amount",
      "leverage",
      "stop_loss",
      "take_profit",
    ];

    console.log("Updating order from form inputs...");
    console.log("Number of inputs:", inputs.length);

    // Find select elements for exchange, side, type
    const exchangeSelect = row.querySelector("td:nth-child(2) select");
    const sideSelect = row.querySelector("td:nth-child(3) select");
    const typeSelect = row.querySelector("td:nth-child(4) select");

    // Find input elements for other fields
    const priceInput = row.querySelector("td:nth-child(5) input");
    const amountInput = row.querySelector("td:nth-child(6) input");
    const leverageInput = row.querySelector("td:nth-child(7) input");
    const stopLossInput = row.querySelector("td:nth-child(8) input");
    const takeProfitInput = row.querySelector("td:nth-child(9) input");

    console.log("Found elements:", {
      exchangeSelect: !!exchangeSelect,
      sideSelect: !!sideSelect,
      typeSelect: !!typeSelect,
      priceInput: !!priceInput,
      amountInput: !!amountInput,
      leverageInput: !!leverageInput,
      stopLossInput: !!stopLossInput,
      takeProfitInput: !!takeProfitInput,
    });

    if (exchangeSelect) {
      updatedOrder.exchange = exchangeSelect.value;
      console.log(
        `Exchange: ${updatedOrder.exchange} -> ${exchangeSelect.value}`
      );
    }

    if (sideSelect) {
      updatedOrder.side = sideSelect.value;
      console.log(`Side: ${updatedOrder.side} -> ${sideSelect.value}`);
    }

    if (typeSelect) {
      updatedOrder.type = typeSelect.value;
      console.log(`Type: ${updatedOrder.type} -> ${typeSelect.value}`);
    }

    if (priceInput) {
      updatedOrder.price = parseFloat(priceInput.value) || 0;
      console.log(`Price: ${updatedOrder.price} -> ${priceInput.value}`);
    }

    if (amountInput) {
      updatedOrder.amount = parseFloat(amountInput.value) || 0;
      console.log(`Amount: ${updatedOrder.amount} -> ${amountInput.value}`);
    }

    if (leverageInput) {
      updatedOrder.leverage = parseFloat(leverageInput.value) || 1;
      console.log(
        `Leverage: ${updatedOrder.leverage} -> ${leverageInput.value}`
      );
    }

    if (stopLossInput) {
      updatedOrder.stop_loss = parseFloat(stopLossInput.value) || 0;
      console.log(
        `Stop Loss: ${updatedOrder.stop_loss} -> ${stopLossInput.value}`
      );
    }

    if (takeProfitInput) {
      updatedOrder.take_profit = parseFloat(takeProfitInput.value) || 0;
      console.log(
        `Take Profit: ${updatedOrder.take_profit} -> ${takeProfitInput.value}`
      );
    }

    console.log("Updated order data:", updatedOrder);

    // Ensure all required fields are present with default values
    const requiredFields = {
      pls: 0,
      pls_percentage: 0,
      price_liquidation: 0,
      take_profit_pls: 0,
      stop_loss_pls: 0,
    };

    Object.keys(requiredFields).forEach((field) => {
      if (!(field in updatedOrder)) {
        updatedOrder[field] = requiredFields[field];
        console.log(`Added missing field ${field}: ${requiredFields[field]}`);
      }
    });

    console.log("Final updated order data:", updatedOrder);

    // Validate the updated order data
    if (!window.app.availableExchanges.includes(updatedOrder.exchange)) {
      console.error(
        "Invalid exchange in updated order:",
        updatedOrder.exchange
      );
      alert(
        `Please select a valid exchange. Available: ${window.app.availableExchanges.join(
          ", "
        )}`
      );
      return;
    }

    if (!window.app.availableSymbols.includes(updatedOrder.symbol)) {
      console.error("Invalid symbol in updated order:", updatedOrder.symbol);
      alert(
        `Please select a valid symbol. Available: ${window.app.availableSymbols.join(
          ", "
        )}`
      );
      return;
    }

    // Show confirmation modal with updated data
    this.showConfirmationModal(
      "save",
      updatedOrder,
      `Are you sure you want to save changes to this ${type.slice(0, -1)}?`
    );
  }

  // Close order function
  closeOrder(symbol, type, index) {
    const symbolData = this.ordersData.find((data) => data.symbol === symbol);
    if (!symbolData) return;

    let order;
    if (type === "orders" && symbolData.active?.orders) {
      order = symbolData.active.orders[index];
      console.log(`Found order in orders array at index ${index}:`, order);
    } else if (type === "positions" && symbolData.active?.positions) {
      order = symbolData.active.positions[index];
      console.log(`Found order in positions array at index ${index}:`, order);
    }

    if (!order) {
      console.error(
        `Order not found for symbol ${symbol}, type ${type}, index ${index}`
      );
      return;
    }

    // Show confirmation modal
    this.showConfirmationModal(
      "close",
      order,
      `Are you sure you want to close this ${type.slice(0, -1)}?`
    );
  }

  // Show confirmation modal
  showConfirmationModal(operation, orderData, message) {
    const modal = document.getElementById("confirmationModal");
    const title = document.getElementById("confirmationTitle");
    const messageEl = document.getElementById("confirmationMessage");
    const detailsEl = document.getElementById("orderDetails");
    const confirmBtn = document.getElementById("confirmationConfirmBtn");

    if (modal && title && messageEl && detailsEl && confirmBtn) {
      title.textContent =
        operation === "save" ? "Confirm Save" : "Confirm Delete";
      messageEl.textContent = message;

      // Display order details using template
      const orderDetailsData = {
        symbol: orderData.symbol || "N/A",
        exchange: orderData.exchange || "N/A",
        side: orderData.side || "N/A",
        type: orderData.type || "N/A",
        price: orderData.price || "N/A",
        amount: orderData.amount || "N/A"
      };

      detailsEl.innerHTML = window.app.renderTemplate('templates/content/order_details_modal.html', orderDetailsData);

      confirmBtn.dataset.operation = operation;
      confirmBtn.dataset.orderData = JSON.stringify(orderData);
      modal.style.display = "block";
    }
  }

  // Save new order
  saveNewOrder() {
    const form = document.getElementById("addOrderForm");
    if (!form) return;

    // Get form values with debugging
    const symbol = document.getElementById("newOrderSymbol").value;
    const exchange = document.getElementById("newOrderExchange").value;
    const side = document.getElementById("newOrderSide").value;
    const type = document.getElementById("newOrderType").value;
    const openType = document.getElementById("newOrderOpenType").value;
    const leverage = document.getElementById("newOrderLeverage").value;
    const price = document.getElementById("newOrderPrice").value;
    const amount = document.getElementById("newOrderAmount").value;

    console.log("Form values collected:", {
      symbol,
      exchange,
      side,
      type,
      openType,
      leverage,
      price,
      amount,
    });

    const orderData = {
      symbol: symbol,
      exchange: exchange,
      side: side,
      type: type,
      open_type: openType,
      leverage: parseFloat(leverage) || 1,
      price: parseFloat(price) || 0,
      amount: parseFloat(amount) || 0,
      stop_loss:
        parseFloat(document.getElementById("newOrderStopLoss").value) || 0,
      take_profit:
        parseFloat(document.getElementById("newOrderTakeProfit").value) || 0,
      fee: parseFloat(document.getElementById("newOrderFee").value) || 0.001,
      amount_usdt:
        parseFloat(document.getElementById("newOrderAmountUsdt").value) || 0,
      // Auto-generated fields with default values
      pls: 0,
      pls_percentage: 0,
      price_liquidation: 0,
      take_profit_pls: 0,
      stop_loss_pls: 0,
      date: new Date().toISOString().slice(0, 19).replace("T", " "),
    };

    // Validate required fields and log the validation
    console.log("Validating order data:", orderData);

    if (
      !orderData.symbol ||
      !orderData.exchange ||
      !orderData.side ||
      !orderData.type
    ) {
      console.error("Validation failed - missing required fields:", {
        symbol: !orderData.symbol,
        exchange: !orderData.exchange,
        side: !orderData.side,
        type: !orderData.type,
        open_type: !orderData.open_type,
      });
      alert("Please fill in all required fields");
      return;
    }

    // Set default open_type if empty
    if (!orderData.open_type) {
      orderData.open_type = "isolated";
      console.log("Set default open_type to:", orderData.open_type);
    }

    // Validate that exchange, side, type, and symbol have valid values
    if (!window.app.availableExchanges.includes(orderData.exchange)) {
      console.error(
        "Invalid exchange:",
        orderData.exchange,
        "Available:",
        window.app.availableExchanges
      );
      alert(
        `Please select a valid exchange. Available: ${window.app.availableExchanges.join(
          ", "
        )}`
      );
      return;
    }

    if (!window.app.availableSymbols.includes(orderData.symbol)) {
      console.error(
        "Invalid symbol:",
        orderData.symbol,
        "Available:",
        window.app.availableSymbols
      );
      alert(
        `Please select a valid symbol. Available: ${window.app.availableSymbols.join(
          ", "
        )}`
      );
      return;
    }

    const validSides = ["long", "short"];
    const validTypes = ["market", "limit"];

    if (!validSides.includes(orderData.side)) {
      console.error("Invalid side:", orderData.side);
      alert("Please select a valid side (Long or Short)");
      return;
    }

    if (!validTypes.includes(orderData.type)) {
      console.error("Invalid type:", orderData.type);
      alert("Please select a valid type (Market or Limit)");
      return;
    }

    console.log("Order data validated successfully:", orderData);

    // Generate new ID
    const maxId = Math.max(
      ...this.ordersData.flatMap((symbolData) => [
        ...(symbolData.active?.orders || []).map((o) => o.id || 0),
        ...(symbolData.active?.positions || []).map((p) => p.id || 0),
        ...(symbolData.closed || []).map((c) => c.id || 0),
      ])
    );
    orderData.id = maxId + 1;

    // Add to orders data based on order type
    let symbolExists = false;
    for (let symbolData of this.ordersData) {
      if (symbolData.symbol === orderData.symbol) {
        symbolExists = true;
        if (!symbolData.active)
          symbolData.active = { orders: [], positions: [] };

        // Add to appropriate array based on order type
        if (orderData.type === "market") {
          if (!symbolData.active.positions) symbolData.active.positions = [];
          symbolData.active.positions.push(orderData);
          console.log(
            `Added market order to positions for ${orderData.symbol}`
          );
        } else if (orderData.type === "limit") {
          if (!symbolData.active.orders) symbolData.active.orders = [];
          symbolData.active.orders.push(orderData);
          console.log(`Added limit order to orders for ${orderData.symbol}`);
        }
        break;
      }
    }

    if (!symbolExists) {
      this.ordersData.push({
        symbol: orderData.symbol,
        active: {
          orders: orderData.type === "limit" ? [orderData] : [],
          positions: orderData.type === "market" ? [orderData] : [],
        },
        closed: [],
      });
      console.log(
        `Created new symbol entry for ${orderData.symbol} with ${orderData.type} order`
      );
    }

    // Save to server
    fetch("/api/orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ orders: this.ordersData }),
    })
      .then((response) => response.json())
      .then((result) => {
        if (result.status === "success") {
          const addOrderForm = document.getElementById("addOrderForm");
          if (addOrderForm) {
            addOrderForm.style.display = "none";
          }
          this.clearNewOrderForm();
          this.renderOrdersTable();
        } else {
          alert("Error saving order: " + result.message);
        }
      })
      .catch((error) => {
        console.error("Error saving order:", error);
        alert("Error saving order");
      });
  }
}

// Create global orders manager instance
window.ordersManager = new OrdersManager();
