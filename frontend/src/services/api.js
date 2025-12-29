import axios from 'axios';

// Base API URL - uses proxy in development (configured in package.json)
const API_BASE_URL = '/api';

// API service for skill operations
const skillService = {
  // Get all skills
  getAllSkills: async () => {
    const response = await axios.get(`${API_BASE_URL}/skills/`);
    return response.data;
  },

  // Get a single skill by ID
  getSkill: async (id) => {
    const response = await axios.get(`${API_BASE_URL}/skills/${id}`);
    return response.data;
  },

  // Create a root skill
  createRootSkill: async (name) => {
    const response = await axios.post(`${API_BASE_URL}/skills/`, {
      name,
      parent_id: null
    });
    return response.data;
  },

  // Create a subskill under a parent
  createSubskill: async (parentId, name) => {
    const response = await axios.post(`${API_BASE_URL}/skills/${parentId}/children`, {
      name
    });
    return response.data;
  },

  // Update a skill
  updateSkill: async (id, updates) => {
    const response = await axios.patch(`${API_BASE_URL}/skills/${id}`, updates);
    return response.data;
  },

  // Delete a skill (and its subtree)
  deleteSkill: async (id) => {
    await axios.delete(`${API_BASE_URL}/skills/${id}`);
  },

  // Get skill summary with aggregated counters
  getSkillSummary: async (id) => {
    const response = await axios.get(`${API_BASE_URL}/skills/${id}/summary`);
    return response.data;
  },

  // Get aggregated summaries for all root skills
  getRootSummaries: async () => {
    const response = await axios.get(`${API_BASE_URL}/skills/roots/summary`);
    return response.data;
  },

  // Import skill tree(s) from JSON
  importSkillTree: async (trees) => {
    const response = await axios.post(`${API_BASE_URL}/skills/import`, trees);
    return response.data;
  },

  // Export all skill trees to JSON
  exportSkillTree: async () => {
    const response = await axios.get(`${API_BASE_URL}/skills/export`);
    return response.data;
  },

  // Replace all skills with imported tree(s)
  updateSkillTree: async (trees) => {
    const response = await axios.put(`${API_BASE_URL}/skills/import`, trees);
    return response.data;
  }
};

// API service for counter operations
const counterService = {
  // Get all counters for a skill
  getCountersBySkill: async (skillId) => {
    const response = await axios.get(`${API_BASE_URL}/counters/?skill_id=${skillId}`);
    return response.data;
  },

  // Get all counters
  getAllCounters: async () => {
    const response = await axios.get(`${API_BASE_URL}/counters/`);
    return response.data;
  },

  // Get a single counter by ID
  getCounter: async (id) => {
    const response = await axios.get(`${API_BASE_URL}/counters/${id}`);
    return response.data;
  },

  // Create a counter
  createCounter: async (skillId, counterData) => {
    const response = await axios.post(`${API_BASE_URL}/counters/?skill_id=${skillId}`, counterData);
    return response.data;
  },

  // Update a counter
  updateCounter: async (id, updates) => {
    const response = await axios.patch(`${API_BASE_URL}/counters/${id}`, updates);
    return response.data;
  },

  // Delete a counter
  deleteCounter: async (id) => {
    await axios.delete(`${API_BASE_URL}/counters/${id}`);
  },

  // Increment counter value
  incrementCounter: async (id, amount = 1.0) => {
    const response = await axios.post(`${API_BASE_URL}/counters/${id}/increment?amount=${amount}`);
    return response.data;
  },

  // Clear all data (skills and counters)
  clearAllData: async () => {
    const response = await axios.delete(`${API_BASE_URL}/data`);
    return response.data;
  }
};

export { skillService, counterService };
export default skillService;
