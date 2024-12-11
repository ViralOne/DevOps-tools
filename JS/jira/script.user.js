// ==UserScript==
// @name         Ticket Assignee Popup
// @namespace    http://tampermonkey.net/
// @version      1.5
// @description  Show a draggable popup with tickets assigned, with a retry button
// @author       Marian
// @match        https://*.atlassian.net/jira/software/c/projects/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function getAllTickets() {
        // Select all ticket card elements
        const ticketCards = document.querySelectorAll('[data-testid="platform-board-kit.ui.card.card"]');
        const tickets = [];

        // Loop through each card and extract the name and ID
        ticketCards.forEach(card => {
            const ticketIdElement = card.querySelector('[data-testid="platform-card.common.ui.key.key"] a span');
            const ticketNameElement = card.querySelector('.yse7za_summary');

            if (ticketIdElement && ticketNameElement) {
                const ticketId = ticketIdElement.textContent.trim();
                const ticketName = ticketNameElement.textContent.trim();
                tickets.push({ id: ticketId, name: ticketName });
            }
        });

        return tickets;
    }

    // Function to create and show a draggable popup with the ticket data
    function showPopup(tickets) {
        // Remove existing popup if it exists
        const existingPopup = document.querySelector('.ticket-popup');
        if (existingPopup) {
            existingPopup.remove();
        }

        // Create popup element
        const popup = document.createElement('div');
        popup.className = 'ticket-popup';
        popup.style.position = 'fixed';
        popup.style.width = '400px';
        popup.style.height = '220px';
        popup.style.backgroundColor = 'black';
        popup.style.border = '1px solid #ccc';
        popup.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
        popup.style.zIndex = '1000';
        popup.style.padding = '10px';
        popup.style.overflowY = 'auto';
        popup.style.top = '100px';
        popup.style.left = '100px';

        // Add title
        const title = document.createElement('h3');
        title.innerText = 'Tickets';
        title.style.cursor = 'move';
        popup.appendChild(title);

        // Add close button
        const closeButton = document.createElement('span');
        closeButton.innerText = '✖';
        closeButton.style.cursor = 'pointer';
        closeButton.style.float = 'right';
        closeButton.style.fontSize = '20px';
        closeButton.style.color = 'red';
        closeButton.title = 'Close';
        closeButton.addEventListener('click', () => {
            document.body.removeChild(popup);
        });
        title.appendChild(closeButton);

        // Add ticket list in a read-only textarea
        const ticketList = document.createElement('textarea');
        ticketList.style.width = '100%';
        ticketList.style.height = '150px';
        ticketList.style.resize = 'none';
        ticketList.readOnly = true;
        ticketList.value = tickets.length === 0
            ? "No tickets found."
            : tickets.map(ticket => `${ticket.id} - ${ticket.name}`).join('\n');

        popup.appendChild(ticketList);

        // Add retry button
        const retryButton = document.createElement('button');
        retryButton.innerText = 'Retry';
        retryButton.style.marginTop = '10px';
        retryButton.addEventListener('click', () => {
            const updatedTickets = getAllTickets();
            showPopup(updatedTickets);
        });
        popup.appendChild(retryButton);

        // Append popup to body
        document.body.appendChild(popup);

        // Make the title draggable
        let isDragging = false;
        let offsetX, offsetY;

        title.addEventListener('mousedown', (e) => {
            isDragging = true;
            offsetX = e.clientX - popup.getBoundingClientRect().left;
            offsetY = e.clientY - popup.getBoundingClientRect().top;
            title.style.cursor = 'grabbing';
        });

        document.addEventListener('mousemove', (e) => {
            if (isDragging) {
                popup.style.left = `${e.clientX - offsetX}px`;
                popup.style.top = `${e.clientY - offsetY}px`;
            }
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
            title.style.cursor = 'move';
        });
    }

    // Execute the script after a delay
    setTimeout(() => {
        const tickets = getAllTickets();
        showPopup(tickets);
    }, 3000);
})();
