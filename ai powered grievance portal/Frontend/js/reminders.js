/**
 * reminders.js - Reminders functionality for Grievance Portal
 * Date: July 10, 2025
 *
 * This module handles reminder-related functionality for the officer dashboard
 */

const ReminderSystem = {
  /**
   * Loads reminders for the officer dashboard
   * @param {string} department - The department name
   * @returns {Promise} - Promise resolving to reminder data
   */
  loadReminders: async function (department) {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/reminders`, {
        method: "GET",
      });

      return await response.json();
    } catch (error) {
      console.error("Failed to load reminders:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Get reminder statistics
   * @returns {Promise} - Promise resolving to reminder statistics
   */
  getStats: async function () {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/reminder_stats`, {
        method: "GET",
      });

      return await response.json();
    } catch (error) {
      console.error("Failed to load reminder stats:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Manually trigger the reminder check
   * @returns {Promise} - Promise resolving to operation result
   */
  triggerManualCheck: async function () {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/send_reminders`, {
        method: "POST",
      });

      return await response.json();
    } catch (error) {
      console.error("Failed to trigger reminder check:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Format reminder date for display
   * @param {string} dateString - ISO date string
   * @returns {string} - Formatted date string
   */
  formatReminderDate: function (dateString) {
    try {
      const date = new Date(dateString);
      return date.toLocaleString("en-US", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      });
    } catch (e) {
      return dateString; // Return original if parsing fails
    }
  },
};

// Add to global window object if in browser environment
if (typeof window !== "undefined") {
  window.ReminderSystem = ReminderSystem;
}
