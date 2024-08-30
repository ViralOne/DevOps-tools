// ==UserScript==
// @name         Check Missing Working Days
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Check for missing working days
// @author       ViralOne
// @match        https://my.freshbooks.com/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=freshbooks.com
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
  
    // Function to create a notification banner
    function createNotificationBanner(message, isError = false) {
        const banner = document.createElement('div');
        banner.style.position = 'fixed';
        banner.style.top = '0';
        banner.style.left = '50%';
        banner.style.transform = 'translateX(-50%)';
        banner.style.backgroundColor = isError ? '#ff4d4d' : '#4caf50'; // Red for errors, green for success
        banner.style.color = 'white';
        banner.style.padding = '10px 20px';
        banner.style.zIndex = '1000';
        banner.style.borderRadius = '5px';
        banner.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
        banner.style.transition = 'opacity 0.5s';
        banner.style.opacity = '1';
        banner.style.display = 'flex';
        banner.style.justifyContent = 'space-between';
        banner.style.alignItems = 'center';
  
        // Create the message text
        const messageText = document.createElement('span');
        messageText.innerText = message;
        banner.appendChild(messageText);
  
        // Create the close button
        const closeButton = document.createElement('button');
        closeButton.innerText = '✖'; // Close button symbol
        closeButton.style.background = 'none';
        closeButton.style.border = 'none';
        closeButton.style.color = 'white';
        closeButton.style.fontSize = '16px';
        closeButton.style.cursor = 'pointer';
        closeButton.style.marginLeft = '15px';
  
        // Add click event to close the banner
        closeButton.addEventListener('click', () => {
            banner.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(banner);
            }, 500);
        });
        const timeRemoveBanner = 10000;
        banner.appendChild(closeButton);
        document.body.appendChild(banner);
  
        // Fade out the banner after 10 seconds if not closed
        setTimeout(() => {
            if (banner.parentNode) { // Check if the banner is still in the DOM
                banner.style.opacity = '0';
                setTimeout(() => {
                    document.body.removeChild(banner);
                }, 500);
            }
        }, timeRemoveBanner);
    }
  
    // Function to get stored non-billable dates from localStorage
    function getNonBillableDates() {
        const storedDates = localStorage.getItem('nonBillableDates');
        return storedDates ? JSON.parse(storedDates) : [];
    }
  
    // Function to save non-billable dates to localStorage
    function saveNonBillableDate(date) {
        const nonBillableDates = getNonBillableDates();
        if (!nonBillableDates.includes(date)) {
            nonBillableDates.push(date);
            localStorage.setItem('nonBillableDates', JSON.stringify(nonBillableDates));
        }
    }
  
      // Function to create dummy entries for missing days and add non-billable buttons
      function createDummyEntries(missingDays) {
        const table = document.querySelector('.js-time-entry-table');
        if (!table) return;
  
        // Insert dummy entries at the top of the table
        missingDays.forEach(missingDay => {
            const row = document.createElement('div');
            row.className = 'entity-table-row display-table-row';
            row.style.backgroundColor = 'yellow';
  
            // Create a cell with a checkbox
            const checkboxCell = document.createElement('div');
            checkboxCell.className = 'entity-table-body-cell entity-table-cell-first u-verticalAlign--middle js-time-entry-list-row display-table-cell js-time-entry-table-cell-checkbox u-hide--phone form-input js-time-entries-table-row-checkbox form-input--checkbox is-unchecked ember-view';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkboxCell.appendChild(checkbox);
            row.appendChild(checkboxCell);
  
            // Create a cell for the dummy entry
            const nameCell = document.createElement('div');
            nameCell.className = 'entity-table-body-cell u-verticalAlign--middle display-table-cell js-time-entry-table-cell-staff-name entity-table-cell-col-4';
            nameCell.innerHTML = `<div class="initialsAvatar userBorderColor-3 xxsmall u-float--left u-marginRight--half">XX</div><div class="u-truncate">Missing Entry</div><div class="entity-table-body-cell-primary u-truncate js-time-entry-table-date">${missingDay}</div>`;
            row.appendChild(nameCell);
  
            // Add other cells as needed (client, project, service, etc.)
            const clientCell = document.createElement('div');
            clientCell.className = 'entity-table-body-cell entity-table-cell-first u-verticalAlign--middle js-time-entry-list-row display-table-cell js-time-entry-table-cell-client-project u-hide--phone';
            clientCell.innerHTML = '<div class="entity-table-body-cell-primary u-truncate">N/A</div><div class="entity-table-body-cell-secondary u-truncate js-time-entry-table-project">N/A</div>';
            row.appendChild(clientCell);
  
            const serviceCell = document.createElement('div');
            serviceCell.className = 'entity-table-body-cell display-table-cell u-verticalAlign--middle js-time-entry-table-cell-service-note u-hide--phone';
            serviceCell.innerHTML = '<div class="entity-table-body-cell-primary u-truncate js-time-entry-table-service">N/A</div><div class="entity-table-body-cell-secondary u-truncate js-time-entry-table-note">Dummy Entry</div>';
            row.appendChild(serviceCell);
  
            // Create a button to mark the date as non-billable
            const buttonCell = document.createElement('div');
            buttonCell.className = 'js-get-started-modal-button  js-get-started medium button-primary';
            const button = document.createElement('button');
            button.innerText = 'Ignore day';
            button.style.marginLeft = '10px';
            button.addEventListener('click', () => {
                saveNonBillableDate(missingDay);
                createNotificationBanner(`Marked ${missingDay} as non-billable.`, false);
                row.remove(); // Remove the row after marking
            });
  
            buttonCell.appendChild(button);
            row.appendChild(buttonCell);
  
            // Insert the new row at the top of the table
            table.insertBefore(row, table.firstChild);
        });
    }
  
    function checkMissedWorkdays() {
      // Get all date elements from the table
      const dateElements = document.querySelectorAll('.js-time-entry-table-date');
      
      // Extract dates and convert them to Date objects
      const workedDates = Array.from(dateElements).map(el => {
          const dateText = el.textContent.trim();
          return new Date(dateText);
      });
  
      const nonBillableDates = getNonBillableDates();
  
      // Get the current date and the start of the week (Monday)
      const today = new Date();
      const currentDay = today.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
      const startOfWeek = new Date(today);
      startOfWeek.setDate(today.getDate() - (currentDay === 0 ? 6 : currentDay - 1)); // Set to Monday
  
      // Create an array of weekdays (Monday to today)
      const weekdays = [];
      for (let i = 0; i <= (today.getDay() === 0 ? 5 : today.getDay() - 1); i++) {
          const day = new Date(startOfWeek);
          day.setDate(startOfWeek.getDate() + i);
          weekdays.push(day.toDateString());
      }
  
     // Check for missed workdays
      const missedDays = weekdays.filter(weekday => {
        // Check if the weekday is not in workedDates and is not a non-billable date
        return !workedDates.some(workedDate => workedDate.toDateString() === weekday) && 
              !nonBillableDates.includes(weekday);
      });
  
      // Output the result
      if (missedDays.length > 0) {
          createNotificationBanner(`Missed workdays: ${missedDays.join(', ')}`, true);
          createDummyEntries(missedDays);
      } else {
          createNotificationBanner(`No missed workdays found.`, false);
      }
  }
    setTimeout(checkMissedWorkdays, 4000);
  })();
  