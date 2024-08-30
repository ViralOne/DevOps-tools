// ==UserScript==
// @name         Check Missing Working Days
// @namespace    http://tampermonkey.net/
// @version      1.3
// @description  Check for missing working days
// @author       ViralOne
// @match        https://my.freshbooks.com/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=freshbooks.com
// @grant        GM_notification
// ==/UserScript==

(function () {
    "use strict";
  
    let WORKING_HOURS = parseInt(localStorage.getItem("workingHours"), 10) || 8;
    let SEND_END_OF_DAY_NOTIFICATION = localStorage.getItem("sendEndOfDayNotification") === 'true';
    const DELAY_FOR_CHECK = 4000;
    const BANNER_TIMEOUT = 10000;
    let lastPopupTop = 100;
    let popupNumber = 0;
    let settingsOpen = false;
  
    // Utility function to create an element with styles
    function createStyledElement(tag, attributes = {}, innerText = "") {
      const element = document.createElement(tag);
      Object.assign(element.style, attributes);
      if (attributes.value !== undefined) {
        element.value = attributes.value;
      }
      element.innerText = innerText;
      return element;
    }
  
    // Function to create a notification banner
    function createNotificationBanner(message, isError = false) {
      const banner = createStyledElement("div", {
        position: "fixed",
        top: "0",
        left: "50%",
        transform: "translateX(-50%)",
        backgroundColor: isError ? "#ff4d4d" : "#4caf50",
        color: "white",
        padding: "10px 20px",
        zIndex: "1000",
        borderRadius: "5px",
        boxShadow: "0 2px 10px rgba(0, 0, 0, 0.2)",
        transition: "opacity 0.5s",
        opacity: "1",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      });
  
      const closeButton = createStyledElement(
        "button",
        {
          background: "none",
          border: "none",
          color: "white",
          fontSize: "16px",
          cursor: "pointer",
          marginLeft: "15px",
        },
        "✖",
      );
  
      closeButton.addEventListener("click", () => fadeOutBanner(banner));
      banner.appendChild(createStyledElement("span", {}, message));
      banner.appendChild(closeButton);
      document.body.appendChild(banner);
  
      setTimeout(() => fadeOutBanner(banner), BANNER_TIMEOUT);
    }
  
    // Function to fade out and remove the banner
    function fadeOutBanner(banner) {
      banner.style.opacity = "0";
      setTimeout(() => {
        if (banner.parentNode) {
          document.body.removeChild(banner);
        }
      }, 500);
    }
  
    // Function to get stored non-billable dates from localStorage
    function getNonBillableDates() {
      try {
        const storedDates = localStorage.getItem("nonBillableDates");
        return storedDates ? JSON.parse(storedDates) : [];
      } catch (error) {
        createNotificationBanner("Error retrieving non-billable dates:", true);
        return [];
      }
    }
  
    // Function to save non-billable dates to localStorage
    function saveNonBillableDate(date) {
      const nonBillableDates = getNonBillableDates();
      if (!nonBillableDates.includes(date)) {
        nonBillableDates.push(date);
        localStorage.setItem(
          "nonBillableDates",
          JSON.stringify(nonBillableDates),
        );
      }
    }
  
    function getIgnoredHours() {
      try {
        const storedHours = localStorage.getItem("ignoredHours");
        const parsedHours = JSON.parse(storedHours);
        // Ensure that parsedHours is an array
        return Array.isArray(parsedHours) ? parsedHours : [];
      } catch (error) {
        createNotificationBanner("Error retrieving ignored hours:", true);
        return [];
      }
    }
  
    // Function to save ignored hours to localStorage
    function saveIgnoreHours(date, hours) {
      const ignoredHours = getIgnoredHours();
      const existingEntry = ignoredHours.find(entry => entry.date === date);
  
      if (existingEntry) {
        // If the date already exists, update the hours
        existingEntry.hours += hours;
      } else {
        // If the date does not exist, add a new entry
        ignoredHours.push({ date, hours });
      }
  
      localStorage.setItem("ignoredHours", JSON.stringify(ignoredHours));
    }
  
    // Function to create a popup for missed days
    function createSummaryWindow(missingDays, insufficientHours) {
      const popup = createStyledElement("div", {
        position: "fixed",
        top: `${lastPopupTop}px`,
        right: "15px",
        backgroundColor: "white",
        border: "1px solid #ccc",
        borderRadius: "5px",
        boxShadow: "0 2px 10px rgba(0, 0, 0, 0.2)",
        zIndex: "1000",
        padding: "1px",
        maxHeight: "80vh",
        overflowY: "auto",
        width: "250px",
      });
  
      const header = createPopupHeader(popup, "Workday Summary");
      popup.appendChild(header);
  
      if (missingDays.length > 0) {
        const missingDaysHeader = createStyledElement(
          "h4",
          { fontWeight: "bold" },
          "Missing Days",
        );
        popup.appendChild(missingDaysHeader);
        missingDays.forEach((missingDay) =>
          createMissingDayRow(popup, missingDay, 0),
        );
      }
  
      if (Object.keys(insufficientHours).length > 0) {
        const insufficientHoursHeader = createStyledElement(
          "h4",
          { fontWeight: "bold" },
          "Insufficient Hours",
        );
        popup.appendChild(insufficientHoursHeader);
        for (const [day, hours] of Object.entries(insufficientHours)) {
          createMissingDayRow(popup, day, hours);
        }
      }
  
      document.body.appendChild(popup);
      makePopupDraggable(popup, header);
  
      // Update lastPopupTop for the next popup
      lastPopupTop += popup.offsetHeight + 10;
    }
  
    // Function to create a settings panel
    function createSettingsWindow() {
      if (settingsOpen) return;
      popupNumber++;
      settingsOpen = true;
      const panel = createStyledElement("div", {
        position: "fixed",
        top: `${lastPopupTop}px`, // Set the top position based on lastPopupTop
        right: "15px",
        backgroundColor: "white",
        border: "1px solid #ccc",
        borderRadius: "5px",
        boxShadow: "0 2px 10px rgba(0, 0, 0, 0.2)",
        zIndex: "1000",
        padding: "1px",
        maxHeight: "80vh",
        overflowY: "auto",
        width: "250px",
      });
  
      const header = createPopupHeader(panel, "User Preferences");
      panel.appendChild(header);
  
      // Create a container for the content
      const content = createStyledElement("div", {
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      });
  
      // Create a container for the label and input
      const hoursContainer = createStyledElement("div", {
        display: "flex",
        alignItems: "center",
        marginBottom: "10px",
      });
  
      // Working hours label
      const hoursLabel = createStyledElement(
        "label",
        {
          width: "120px",
          marginRight: "10px",
        },
        "Working Hours: ",
      );
      hoursContainer.appendChild(hoursLabel);
  
      // Working hours input
      const hoursInput = createStyledElement("input", {
        type: "number",
        style: { flex: "1" },
      });
      hoursInput.value = WORKING_HOURS;
      hoursContainer.appendChild(hoursInput);
  
      // Append the container to the content
      content.appendChild(hoursContainer);
  
      // sendEndOfDayNotification logic
      const sendEndOfDayNotificationContainer = createStyledElement("div", {
        display: "flex",
        alignItems: "center",
        marginBottom: "10px",
      });
      const sendEndOfDayNotificationLabel = createStyledElement(
        "label",
        {
          width: "120px",
          marginRight: "10px",
        },
        "Notification: ",
      );
      sendEndOfDayNotificationContainer.appendChild(sendEndOfDayNotificationLabel);
  
      // Create the dropdown for notification
      const sendEndOfDayNotificationSelect = createStyledElement("select", {
        style: { flex: "1", marginLeft: "10px" },
      });
      const trueOption = createStyledElement("option", {}, "True");
      const falseOption = createStyledElement("option", {}, "False");
  
      sendEndOfDayNotificationSelect.appendChild(trueOption);
      sendEndOfDayNotificationSelect.appendChild(falseOption);
  
      // Set the selected value based on the SEND_END_OF_DAY_NOTIFICATION variable
      sendEndOfDayNotificationSelect.value = SEND_END_OF_DAY_NOTIFICATION ? "True" : "False";
  
      sendEndOfDayNotificationContainer.appendChild(sendEndOfDayNotificationSelect);
      content.appendChild(sendEndOfDayNotificationContainer);
  
      // View Non-Billable Dates Button
      const viewButton = createStyledElement(
        "button",
        {},
        "View Non-Billable Dates",
      );
      viewButton.addEventListener("click", () => {
        const nonBillableDates = getNonBillableDates();
        alert(
          nonBillableDates.length > 0
            ? `Non-Billable Dates:\n${nonBillableDates.join("\n")}`
            : "No non-billable dates found.",
        );
      });
      content.appendChild(viewButton);
  
      // Reset Non-Billable Dates Button
      const resetButton = createStyledElement(
        "button",
        {},
        "Reset Non-Billable Dates",
      );
      resetButton.addEventListener("click", () => {
        localStorage.removeItem("nonBillableDates");
        createNotificationBanner(`Non-billable dates have been reset.`, false);
      });
      content.appendChild(resetButton);
  
      // --
    // View Ignored Hours Button
    const viewIgnoredHoursButton = createStyledElement(
      "button",
      {},
      "View Ignored Hours",
    );
    viewIgnoredHoursButton.addEventListener("click", () => {
      const nonIgnoredHours = getIgnoredHours();
      console.log(nonIgnoredHours); // Inspect the structure here
      if (nonIgnoredHours.length > 0) {
        // Create a message from the array of objects
        const message = nonIgnoredHours.map(entry => {
          return `Date: ${entry.date}, Hours: ${entry.hours}`;
        }).join("\n");
        alert(`Ignored Hours:\n${message}`);
      } else {
        alert("No Ignored Hours found.");
      }
    });
      content.appendChild(viewIgnoredHoursButton);
  
    // Reset Ignored Hours Button
    const resetIgnoredHoursButton = createStyledElement(
      "button",
      {},
      "Reset Ignored Hours",
    );
    resetIgnoredHoursButton.addEventListener("click", () => {
      localStorage.removeItem("ignoredHours");
      createNotificationBanner(`Ignored Hours have been reset.`, false);
    });
    content.appendChild(resetIgnoredHoursButton);
      // --
  
      // Save button
      const saveButton = createStyledElement(
        "button",
        {
          marginTop: "20px",
          alignSelf: "flex-end",
          backgroundColor: "#4CAF50",
          color: "white",
          border: "none",
          borderRadius: "5px",
          padding: "10px 15px",
          cursor: "pointer",
          fontSize: "16px",
          transition: "background-color 0.3s",
        },
        "Save",
      );
  
      // Add hover effect
      saveButton.addEventListener("mouseover", () => {
        saveButton.style.backgroundColor = "#45a049"; // Darker green on hover
      });
      saveButton.addEventListener("mouseout", () => {
        saveButton.style.backgroundColor = "#4CAF50"; // Original green
      });
  
      saveButton.addEventListener("click", () => {
        const newWorkingHours = parseInt(hoursInput.value, 10);
        if (!isNaN(newWorkingHours) && newWorkingHours > 0) {
          WORKING_HOURS = newWorkingHours; // Update the variable
          localStorage.setItem("workingHours", newWorkingHours); // Save to localStorage
          localStorage.setItem("sendEndOfDayNotification", sendEndOfDayNotificationSelect.value.toLowerCase());
          createNotificationBanner(
            `Working hours set to ${newWorkingHours}.`,
            false,
          );
        } else {
          createNotificationBanner(
            `Please enter a valid number of working hours.`,
            true,
          );
        }
      });
  
      content.appendChild(saveButton);
  
      panel.appendChild(content);
      document.body.appendChild(panel);
  
      // Make the panel draggable
      makePopupDraggable(panel, header);
  
      // Update lastPopupTop for the next panel
      lastPopupTop += panel.offsetHeight + 10; // Add some space between panels
    }
  
    // Function to create the header for the popup
    function createPopupHeader(popup, name) {
      const header = createStyledElement("div", {
        display: "flex",
        justifyContent: "space-around",
        alignItems: "center",
        cursor: "move",
        padding: "5px",
        backgroundColor: "#f1f1f1",
        borderBottom: "1px solid #ccc",
      });
  
      const title = createStyledElement("h3", {}, `${name}`);
      header.appendChild(title);
  
      // Settings button to open the settings panel
      const settingsButton = createStyledElement("button", {}, "⚙️");
      settingsButton.addEventListener("click", () => {
        if (!settingsOpen) {
          createSettingsWindow();
        }
      });
  
      if (popupNumber === 0) {
        header.appendChild(settingsButton);
      }
  
      // Close button for the popup
      const closeButton = createStyledElement("button", {}, "✖");
      closeButton.addEventListener("click", () => {
        const popupHeight = popup.offsetHeight;
        popup.remove();
        popupNumber--;
        settingsOpen = false; // Set to false when the popup is closed
        lastPopupTop -= popupHeight + 10; // Subtract the height of the popup from lastPopupTop
      });
      header.appendChild(closeButton);
  
      return header;
    }
  
    // Function to create a row for each missing day
    function createMissingDayRow(popup, missingDay, hoursWorked) {
      const row = createStyledElement("div", {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "5px",
        borderBottom: "1px solid #eee",
      });
  
      const dateText = createStyledElement(
        "span",
        {},
        hoursWorked > 0 ? `${missingDay}: ${hoursWorked} hours` : missingDay,
      );
  
      const ignoreButton = createStyledElement("button", {}, "Ignore");
      ignoreButton.style.marginLeft = "10px";
  
      if (hoursWorked > 0) {
        ignoreButton.addEventListener("click", () => {
          saveIgnoreHours(missingDay, hoursWorked);
          createNotificationBanner(`Marked ${missingDay} as non-billable.`, false);
          row.remove();
        });
      }
      else
      {
        ignoreButton.addEventListener("click", () => {
          saveNonBillableDate(missingDay);
          createNotificationBanner(`Marked ${missingDay} as non-billable.`, false);
          row.remove();
        });
      }
  
      row.appendChild(dateText);
      row.appendChild(ignoreButton);
      popup.appendChild(row);
    }
  
    // Function to make the popup draggable
    function makePopupDraggable(popup, header) {
      let offsetX, offsetY;
  
      header.addEventListener("mousedown", (e) => {
        offsetX = e.clientX - popup.getBoundingClientRect().left;
        offsetY = e.clientY - popup.getBoundingClientRect().top;
  
        const mouseMoveHandler = (e) => {
          popup.style.left = `${e.clientX - offsetX}px`;
          popup.style.top = `${e.clientY - offsetY}px`;
        };
  
        const mouseUpHandler = () => {
          document.removeEventListener("mousemove", mouseMoveHandler);
          document.removeEventListener("mouseup", mouseUpHandler);
        };
  
        document.addEventListener("mousemove", mouseMoveHandler);
        document.addEventListener("mouseup", mouseUpHandler);
      });
    }
  
    function sendNotification(title, message) {
      GM_notification({
          title: title,
          text: message,
          timeout: 10000,
          onclick: () => {
              window.focus();
              window.location.href = "https://my.freshbooks.com/";
          },
      });
  }
  
    // Function to check missed workdays
    function checkMissedWorkdays() {
      const dateElements = document.querySelectorAll(".js-time-entry-table-date");
      const workedDates = Array.from(dateElements).map(
          (el) => new Date(el.textContent.trim()),
      );
  
      const nonBillableDates = getNonBillableDates();
      const today = new Date();
      const startOfWeek = new Date(today);
      startOfWeek.setDate(
          today.getDate() - (today.getDay() === 0 ? 6 : today.getDay() - 1),
      );
  
      const weekdays = Array.from(
          { length: today.getDay() === 0 ? 6 : today.getDay() },
          (_, i) => {
              const day = new Date(startOfWeek);
              day.setDate(startOfWeek.getDate() + i);
              return day.toDateString();
          },
      );
  
      const missingDays = weekdays.filter(
          (weekday) =>
              !workedDates.some(
                  (workedDate) => workedDate.toDateString() === weekday,
              ) && !nonBillableDates.includes(weekday),
      );
  
      if (missingDays.length > 0) {
          const message = `Reminder: You haven't added time for the following days: ${missingDays.join(", ")}`;
          createNotificationBanner(message, true);
          if (SEND_END_OF_DAY_NOTIFICATION === true) {
            sendNotification("Missing Working Days", message);
          }
      }
  
      return missingDays;
  }
  
  function getWorkedHour() {
    const rows = document.querySelectorAll(".entity-table-row");
    const hoursByDate = {};
    const ignoredHours = getIgnoredHours();
  
    // Create a mapping of ignored hours for easy lookup
    const ignoredHoursMap = ignoredHours.reduce((acc, entry) => {
        acc[entry.date] = (acc[entry.date] || 0) + entry.hours;
        return acc;
    }, {});
  
    rows.forEach((row) => {
        const timeElement = row.querySelector(
            ".entity-table-body-cell-primary.u-truncate.js-time-entry-table-time",
        );
        const dateElement = row.querySelector(".js-time-entry-table-date");
  
        if (timeElement && dateElement) {
            const hoursWorked = parseInt(
                timeElement.textContent.match(/(\d+)h/)?.[1] || 0,
                10,
            );
            const dateWorked = dateElement.textContent.trim();
  
            if (hoursWorked) {
                hoursByDate[dateWorked] =
                    (hoursByDate[dateWorked] || 0) + hoursWorked;
            }
        }
    });
  
    const insufficientHours = {};
    for (const [date, hours] of Object.entries(hoursByDate)) {
        // Check if the date is in the ignored hours map
        if (hours < WORKING_HOURS && !ignoredHoursMap[date]) {
            insufficientHours[date] = hours;
            const message = `Warning: On ${date}, only ${hours} hours were billed.`;
            createNotificationBanner(
              message, true,
            );
          if (SEND_END_OF_DAY_NOTIFICATION === true) {
            sendNotification("Wrong billed time", message);
          }
      }
    }
  
    return insufficientHours;
  }
  
    // Execute the checks
    setTimeout(() => {
      const missingDays = checkMissedWorkdays();
      const insufficientHours = getWorkedHour();
  
      if (missingDays.length > 0 || Object.keys(insufficientHours).length > 0) {
        createSummaryWindow(missingDays, insufficientHours);
      } else {
        createNotificationBanner(`No missed workdays found.`, false);
      }
    }, DELAY_FOR_CHECK);
  })();
  