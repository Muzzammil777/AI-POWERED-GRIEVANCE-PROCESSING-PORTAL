/**
 * main.js - Main JavaScript functions for Mudhalvarin Mugavari Grievance Portal
 * Date: July 9, 2025
 */

// Common utility functions

/**
 * Returns a formatted date string
 * @param {Date} date - Date object to format
 * @returns {string} - Formatted date string (DD-MMM-YYYY)
 */
function formatDate(date) {
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  const day = date.getDate().toString().padStart(2, "0");
  const month = months[date.getMonth()];
  const year = date.getFullYear();

  return `${day}-${month}-${year}`;
}

/**
 * Generates a random grievance ID
 * @returns {string} - Grievance ID in format GR-YYYY-XXX
 */
function generateGrievanceId() {
  const year = new Date().getFullYear();
  const randomNum = Math.floor(Math.random() * 1000)
    .toString()
    .padStart(3, "0");
  return `GR-${year}-${randomNum}`;
}

/**
 * Validates email format
 * @param {string} email - Email to validate
 * @returns {boolean} - True if email is valid
 */
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validates phone number format (10 digits)
 * @param {string} phone - Phone number to validate
 * @returns {boolean} - True if phone is valid
 */
function isValidPhone(phone) {
  const phoneRegex = /^\d{10}$/;
  return phoneRegex.test(phone);
}

/**
 * Displays a notification message
 * @param {string} message - Message to display
 * @param {string} type - Type of message (success, error, warning, info)
 * @param {number} duration - Duration in milliseconds to show message
 */
function showNotification(message, type = "info", duration = 3000) {
  // Check if notification container exists, if not create it
  let notificationContainer = document.getElementById("notification-container");

  if (!notificationContainer) {
    notificationContainer = document.createElement("div");
    notificationContainer.id = "notification-container";
    notificationContainer.style.position = "fixed";
    notificationContainer.style.top = "20px";
    notificationContainer.style.right = "20px";
    notificationContainer.style.zIndex = "1000";
    document.body.appendChild(notificationContainer);
  }

  // Create notification element
  const notification = document.createElement("div");
  notification.className = `notification notification-${type}`;
  notification.innerHTML = message;

  // Style the notification
  notification.style.padding = "15px 20px";
  notification.style.marginBottom = "10px";
  notification.style.borderRadius = "5px";
  notification.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.1)";
  notification.style.fontSize = "14px";
  notification.style.opacity = "0";
  notification.style.transition = "opacity 0.3s ease-in-out";

  // Set colors based on type
  switch (type) {
    case "success":
      notification.style.backgroundColor = "#d4edda";
      notification.style.color = "#155724";
      notification.style.borderLeft = "4px solid #28a745";
      break;
    case "error":
      notification.style.backgroundColor = "#f8d7da";
      notification.style.color = "#721c24";
      notification.style.borderLeft = "4px solid #dc3545";
      break;
    case "warning":
      notification.style.backgroundColor = "#fff3cd";
      notification.style.color = "#856404";
      notification.style.borderLeft = "4px solid #ffc107";
      break;
    default: // info
      notification.style.backgroundColor = "#d1ecf1";
      notification.style.color = "#0c5460";
      notification.style.borderLeft = "4px solid #17a2b8";
  }

  // Add to container
  notificationContainer.appendChild(notification);

  // Animation to show
  setTimeout(() => {
    notification.style.opacity = "1";
  }, 10);

  // Remove after duration
  setTimeout(() => {
    notification.style.opacity = "0";
    setTimeout(() => {
      notificationContainer.removeChild(notification);
    }, 300);
  }, duration);
}

/**
 * Gets URL parameters
 * @param {string} name - Parameter name to get
 * @returns {string|null} - Parameter value or null
 */
function getUrlParam(name) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(name);
}

/**
 * Navigation function for login options
 * @param {string} pageType - Type of page to navigate to
 */
function navigateTo(pageType) {
  switch (pageType) {
    case "citizen":
      window.location.href = "login.html";
      break;
    case "officer":
      window.location.href = "officer_login.html";
      break;
    case "file":
      window.location.href = "file_grievance.html";
      break;
    case "track":
      window.location.href = "track_grievance.html";
      break;
    default:
      window.location.href = "index.html";
  }
}

// Initialize any common elements when the page loads
document.addEventListener("DOMContentLoaded", function () {
  // Add event listeners to any common elements that might exist on multiple pages
  const submitButtons = document.querySelectorAll(".form-submit");
  if (submitButtons) {
    submitButtons.forEach((button) => {
      button.addEventListener("mouseenter", () => {
        button.style.transform = "translateY(-2px)";
      });
      button.addEventListener("mouseleave", () => {
        button.style.transform = "translateY(0)";
      });
    });
  }

  // Setup accessibility features
  setupAccessibility();
});

/**
 * Setup accessibility features
 */
function setupAccessibility() {
  // Add focus indicators for keyboard navigation
  const focusableElements = document.querySelectorAll(
    'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  focusableElements.forEach((element) => {
    element.addEventListener("focus", () => {
      element.style.outline = "2px solid #27ae60";
      element.style.outlineOffset = "2px";
    });

    element.addEventListener("blur", () => {
      element.style.outline = "";
    });
  });
}
