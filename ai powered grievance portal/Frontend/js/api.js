/**
 * api.js - API integration for Mudhalvarin Mugavari Grievance Portal
 * Date: July 9, 2025
 */

// API Configuration
const API_BASE_URL = "http://localhost:8000"; // Change this to match your FastAPI server address

/**
 * API Client for Mudhalvarin Mugavari Grievance Portal
 */
const ApiClient = {
  /**
   * Login a user or officer
   * @param {string} username - The username
   * @param {string} password - The password
   * @returns {Promise} - Response from API
   */
  login: async function (username, password) {
    try {
      const formData = new FormData();
      formData.append("user_id", username);
      formData.append("passcode", password);

      const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        body: formData,
      });

      return await response.json();
    } catch (error) {
      console.error("Login error:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Register a new user
   * @param {string} fullName - User's full name
   * @param {string} username - The username
   * @param {string} password - The password
   * @returns {Promise} - Response from API
   */
  register: async function (fullName, username, password) {
    try {
      const formData = new FormData();
      formData.append("full_name", fullName);
      formData.append("new_user", username);
      formData.append("new_pass", password);

      const response = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        body: formData,
      });

      return await response.json();
    } catch (error) {
      console.error("Registration error:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Classify a petition to determine the appropriate department
   * @param {string} petitionText - The petition text to classify
   * @returns {Promise} - Response from API with category
   */
  classifyPetition: async function (petitionText) {
    try {
      const formData = new FormData();
      formData.append("petition_text", petitionText);

      const response = await fetch(`${API_BASE_URL}/classify`, {
        method: "POST",
        body: formData,
      });

      return await response.json();
    } catch (error) {
      console.error("Classification error:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Lightweight real-time classification for UI responsiveness
   * @param {string} petitionText - The petition text to classify
   * @returns {Promise} - Response from API with category
   */
  classifyRealtimePetition: async function (petitionText) {
    try {
      const formData = new FormData();
      formData.append("petition_text", petitionText);

      const response = await fetch(`${API_BASE_URL}/classify_realtime`, {
        method: "POST",
        body: formData,
      });

      return await response.json();
    } catch (error) {
      console.error("Real-time classification error:", error);
      return { error: "Classification failed" };
    }
  },

  /**
   * Submit a petition to the appropriate department
   * @param {Object} petitionData - The petition data
   * @returns {Promise} - Response from API
   */
  submitPetition: async function (petitionData) {
    try {
      const formData = new FormData();
      formData.append("name", petitionData.name);
      formData.append("phone", petitionData.phone);
      formData.append("address", petitionData.address || "");
      formData.append("district", petitionData.district || "");
      formData.append("petition_type", "General");
      formData.append("petition_subject", petitionData.subject);
      formData.append("petition_description", petitionData.description);
      formData.append("category", petitionData.category || "General");

      if (petitionData.attachment) {
        formData.append("attachment", petitionData.attachment);
      }

      const response = await fetch(`${API_BASE_URL}/submit_to_department`, {
        method: "POST",
        body: formData,
      });

      return await response.json();
    } catch (error) {
      console.error("Petition submission error:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Get petitions for an admin/officer dashboard
   * @param {string} department - The department name
   * @returns {Promise} - Response from API with petitions
   */
  getAdminPetitions: async function (department) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/petitions?department=${encodeURIComponent(
          department
        )}`,
        {
          method: "GET",
        }
      );

      return await response.json();
    } catch (error) {
      console.error("Get admin petitions error:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Get petitions for an admin/officer dashboard filtered by priority
   * @param {string} department - The department name
   * @param {string} priority - Optional priority to filter by (High, Medium, Low)
   * @returns {Promise} - Response from API with filtered petitions
   */
  getAdminPetitionsByPriority: async function (department, priority) {
    try {
      let url = `${API_BASE_URL}/admin/petitions/by_priority?department=${encodeURIComponent(
        department
      )}`;

      if (priority) {
        url += `&priority=${encodeURIComponent(priority)}`;
      }

      const response = await fetch(url, {
        method: "GET",
      });

      return await response.json();
    } catch (error) {
      console.error("Get petitions by priority error:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Track a grievance by ID and phone number
   * @param {string} grievanceId - The grievance ID to track
   * @param {string} phone - Phone number for verification
   * @returns {Promise} - Response from API with grievance status
   */
  trackGrievance: async function (grievanceId, phone) {
    try {
      const formData = new FormData();
      formData.append("grievance_id", grievanceId);
      formData.append("phone", phone);

      const response = await fetch(`${API_BASE_URL}/track_grievance`, {
        method: "POST",
        body: formData,
      });

      return await response.json();
    } catch (error) {
      console.error("Grievance tracking error:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Update grievance status as officer
   * @param {string} grievanceId - The grievance ID to update
   * @param {string} status - New status (pending, in_progress, resolved, rejected)
   * @param {string} department - Department name
   * @param {string} comment - Optional comment about the status update
   * @returns {Promise} - Response from API with update status
   */
  updateGrievanceStatus: async function (
    grievanceId,
    status,
    department,
    comment = ""
  ) {
    try {
      const formData = new FormData();
      formData.append("grievance_id", grievanceId);
      formData.append("status", status);
      formData.append("department", department);
      formData.append("comment", comment);

      const response = await fetch(`${API_BASE_URL}/update_grievance_status`, {
        method: "POST",
        body: formData,
      });

      return await response.json();
    } catch (error) {
      console.error("Grievance update error:", error);
      return { error: "Network error. Please try again." };
    }
  },

  // --------------------------- New API Methods for Enhanced Features ---------------------------

  /**
   * Get timeline for a specific grievance
   * @param {string} trackingId - The tracking ID of the grievance
   * @param {string} department - The department name
   * @returns {Promise} - Response from API with timeline data
   */
  getGrievanceTimeline: async function (trackingId, department) {
    try {
      const params = new URLSearchParams({
        tracking_id: trackingId,
        department: department,
      });

      const response = await fetch(
        `${API_BASE_URL}/grievance/timeline?${params}`,
        {
          method: "GET",
        }
      );

      return await response.json();
    } catch (error) {
      console.error("Timeline retrieval error:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Check for similar grievances
   * @param {string} department - The department name
   * @param {string} text - The petition text to check
   * @param {number} threshold - Similarity threshold (default 0.8)
   * @returns {Promise} - Response from API with similar grievances
   */
  checkSimilarGrievances: async function (department, text, threshold = 0.8) {
    try {
      const params = new URLSearchParams({
        department: department,
        text: text,
        threshold: threshold,
      });

      const response = await fetch(
        `${API_BASE_URL}/grievance/similar?${params}`,
        {
          method: "GET",
        }
      );

      return await response.json();
    } catch (error) {
      console.error("Similarity check error:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Get notification logs for admin
   * @param {number} limit - Number of notifications to retrieve (default 50)
   * @returns {Promise} - Response from API with notification logs
   */
  getNotificationLogs: async function (limit = 50) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/notifications?limit=${limit}`,
        {
          method: "GET",
        }
      );

      return await response.json();
    } catch (error) {
      console.error("Notification logs error:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Test similarity detection system
   * @returns {Promise} - Response from API with test results
   */
  testSimilarityDetection: async function () {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/test_similarity`, {
        method: "POST",
      });

      return await response.json();
    } catch (error) {
      console.error("Similarity test error:", error);
      return { error: "Network error. Please try again." };
    }
  },

  /**
   * Test notification system
   * @returns {Promise} - Response from API with test results
   */
  testNotificationSystem: async function () {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/test_notifications`, {
        method: "POST",
      });

      return await response.json();
    } catch (error) {
      console.error("Notification test error:", error);
      return { error: "Network error. Please try again." };
    }
  },
};
