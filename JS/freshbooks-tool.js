// ==UserScript==
// @name         Check Missing Working Days
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Check for missing working days
// @author       ViralOne
// @match        https://my.freshbooks.com/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=freshbooks.com
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
  
    const WORKING_HOURS = 8;
    const DELAY_FOR_CHECK = 4000;
    const BANNER_TIMEOUT = 10000;
  
    // Utility function to create an element with styles
    function createStyledElement(tag, styles = {}, innerText = '') {
        const element = document.createElement(tag);
        Object.assign(element.style, styles);
        element.innerText = innerText;
        return element;
    }
  
    // Function to create a notification banner
    function createNotificationBanner(message, isError = false) {
        const banner = createStyledElement('div', {
            position: 'fixed',
            top: '0',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: isError ? '#ff4d4d' : '#4caf50',
            color: 'white',
            padding: '10px 20px',
            zIndex: '1000',
            borderRadius: '5px',
            boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)',
            transition: 'opacity 0.5s',
            opacity: '1',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
        });
  
        const closeButton = createStyledElement('button', {
            background: 'none',
            border: 'none',
            color: 'white',
            fontSize: '16px',
            cursor: 'pointer',
            marginLeft: '15px'
        }, '✖');
  
        closeButton.addEventListener('click', () => fadeOutBanner(banner));
        banner.appendChild(createStyledElement('span', {}, message));
        banner.appendChild(closeButton);
        document.body.appendChild(banner);
  
        setTimeout(() => fadeOutBanner(banner), BANNER_TIMEOUT);
    }
  
    // Function to fade out and remove the banner
    function fadeOutBanner(banner) {
        banner.style.opacity = '0';
        setTimeout(() => {
            if (banner.parentNode) {
                document.body.removeChild(banner);
            }
        }, 500);
    }
  
    // Function to get stored non-billable dates from localStorage
    function getNonBillableDates() {
        try {
            const storedDates = localStorage.getItem('nonBillableDates');
            return storedDates ? JSON.parse(storedDates) : [];
        } catch (error) {
            console.error('Error retrieving non-billable dates:', error);
            return [];
        }
    }
  
    // Function to save non-billable dates to localStorage
    function saveNonBillableDate(date) {
        const nonBillableDates = getNonBillableDates();
        if (!nonBillableDates.includes(date)) {
            nonBillableDates.push(date);
            localStorage.setItem('nonBillableDates', JSON.stringify(nonBillableDates));
        }
    }
  
    // Function to create a popup for missed days
    function createPopup(missingDays, insufficientHours) {
        const popup = createStyledElement('div', {
            position: 'fixed',
            top: '100px',
            right: '15px',
            backgroundColor: 'white',
            border: '1px solid #ccc',
            borderRadius: '5px',
            boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)',
            zIndex: '1000',
            padding: '10px',
            maxHeight: '80vh',
            overflowY: 'auto',
            width: '250px'
        });
  
        const header = createPopupHeader(popup);
        popup.appendChild(header);
  
        if (missingDays.length > 0) {
            const missingDaysHeader = createStyledElement('h4', { fontWeight: 'bold' }, 'Missing Days');
            popup.appendChild(missingDaysHeader);
            missingDays.forEach(missingDay => createMissingDayRow(popup, missingDay, 0));
        }
  
        if (Object.keys(insufficientHours).length > 0) {
            const insufficientHoursHeader = createStyledElement('h4', { fontWeight: 'bold' }, 'Insufficient Hours');
            popup.appendChild(insufficientHoursHeader);
            for (const [day, hours] of Object.entries(insufficientHours)) {
                createMissingDayRow(popup, day, hours);
            }
        }
  
        document.body.appendChild(popup);
        makePopupDraggable(popup, header);
    }
  
    // Function to create the header for the popup
    function createPopupHeader(popup) {
        const header = createStyledElement('div', {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'move',
            padding: '5px',
            backgroundColor: '#f1f1f1',
            borderBottom: '1px solid #ccc'
        });
  
        const title = createStyledElement('h3', {}, 'Workday Summary');
        header.appendChild(title);
  
        const closeButton = createStyledElement('button', {}, '✖');
        closeButton.addEventListener('click', () => popup.remove());
        header.appendChild(closeButton);
        return header;
    }
  
    // Function to create a row for each missing day
    function createMissingDayRow(popup, missingDay, hoursWorked) {
        const row = createStyledElement('div', {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '5px',
            borderBottom: '1px solid #eee'
        });
  
        const dateText = createStyledElement('span', {}, hoursWorked > 0 ? `${missingDay}: ${hoursWorked} hours` : missingDay);
        const ignoreButton = createStyledElement('button', {}, 'Ignore');
  
        ignoreButton.style.marginLeft = '10px';
        ignoreButton.addEventListener('click', () => {
            saveNonBillableDate(missingDay);
            createNotificationBanner(`Marked ${missingDay} as non-billable.`, false);
            row.remove();
        });
  
        row.appendChild(dateText);
        row.appendChild(ignoreButton);
        popup.appendChild(row);
    }
  
    // Function to make the popup draggable
    function makePopupDraggable(popup, header) {
        header.addEventListener('mousedown', (e) => {
            let offsetX = e.clientX - popup.getBoundingClientRect().left;
            let offsetY = e.clientY - popup.getBoundingClientRect().top;
  
            const mouseMoveHandler = (e) => {
                popup.style.left = `${e.clientX - offsetX}px`;
                popup.style.top = `${e.clientY - offsetY}px`;
            };
  
            const mouseUpHandler = () => {
                document.removeEventListener('mousemove', mouseMoveHandler);
                document.removeEventListener('mouseup', mouseUpHandler);
            };
  
            document.addEventListener('mousemove', mouseMoveHandler);
            document.addEventListener('mouseup', mouseUpHandler);
        });
    }
  
    // Function to check missed workdays
    function checkMissedWorkdays() {
        const dateElements = document.querySelectorAll('.js-time-entry-table-date');
        const workedDates = Array.from(dateElements).map(el => new Date(el.textContent.trim()));
  
        const nonBillableDates = getNonBillableDates();
        const today = new Date();
        const startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - (today.getDay() === 0 ? 6 : today.getDay() - 1));
  
        const weekdays = Array.from({ length: today.getDay() === 0 ? 6 : today.getDay() }, (_, i) => {
            const day = new Date(startOfWeek);
            day.setDate(startOfWeek.getDate() + i);
            return day.toDateString();
        });
  
        return weekdays.filter(weekday =>
            !workedDates.some(workedDate => workedDate.toDateString() === weekday) &&
            !nonBillableDates.includes(weekday)
        );
    }
  
    // Function to check worked hours
    function getWorkedHour() {
        const rows = document.querySelectorAll('.entity-table-row');
        const hoursByDate = {};
  
        rows.forEach(row => {
            const timeElement = row.querySelector('.entity-table-body-cell-primary.u-truncate.js-time-entry-table-time');
            const dateElement = row.querySelector('.js-time-entry-table-date');
  
            if (timeElement && dateElement) {
                const hoursWorked = parseInt(timeElement.textContent.match(/(\d+)h/)?.[1] || 0, 10);
                const dateWorked = dateElement.textContent.trim();
  
                if (hoursWorked) {
                    hoursByDate[dateWorked] = (hoursByDate[dateWorked] || 0) + hoursWorked;
                }
            }
        });
  
        const insufficientHours = {};
        for (const [date, hours] of Object.entries(hoursByDate)) {
            if (hours < WORKING_HOURS) {
                insufficientHours[date] = hours;
                createNotificationBanner(`Warning: On ${date}, only ${hours} hours were billed.`, true);
            }
        }
  
        return insufficientHours;
    }
  
    // Execute the checks
    setTimeout(() => {
        const missingDays = checkMissedWorkdays();
        const insufficientHours = getWorkedHour();
  
        if (missingDays.length > 0 || Object.keys(insufficientHours).length > 0) {
            createPopup(missingDays, insufficientHours);
        } else {
            createNotificationBanner(`No missed workdays found.`, false);
        }
    }, DELAY_FOR_CHECK);
  })();
  