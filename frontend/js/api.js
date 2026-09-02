/**
 * ProcessPulse API Client
 * Encapsulates all backend REST API communication using modern ES6+ async/await.
 */

const API_BASE = '/api/v1';

class ApiClient {
  constructor() {
    this.token = sessionStorage.getItem('process_pulse_token') || null;
  }

  setToken(token) {
    this.token = token;
    if (token) {
      sessionStorage.setItem('process_pulse_token', token);
    } else {
      sessionStorage.removeItem('process_pulse_token');
    }
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token ? { 'Authorization': `Bearer ${this.token}` } : {}),
      ...options.headers,
    };

    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `HTTP error ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`[API Error] ${endpoint}:`, error);
      throw error;
    }
  }

  // Analytics APIs
  async getOverviewKPIs(processId = 'ONBOARD_V1') {
    return this.request(`/analytics/overview?process_id=${processId}`);
  }

  async getBottlenecks(processId = 'ONBOARD_V1') {
    return this.request(`/analytics/bottlenecks?process_id=${processId}`);
  }

  async getDepartments(processId = 'ONBOARD_V1') {
    return this.request(`/analytics/departments?process_id=${processId}`);
  }

  async getSlaDistribution(processId = 'ONBOARD_V1') {
    return this.request(`/analytics/sla?process_id=${processId}`);
  }

  // Process Mining APIs
  async getDFG(processId = 'ONBOARD_V1') {
    return this.request(`/process-mining/dfg?process_id=${processId}`);
  }

  async getVariants(processId = 'ONBOARD_V1') {
    return this.request(`/process-mining/variants?process_id=${processId}`);
  }

  // Predictive ML APIs
  async getTriageQueue(processId = 'ONBOARD_V1') {
    return this.request(`/prediction/triage-queue?process_id=${processId}`);
  }

  async predictCase(caseData) {
    return this.request('/prediction/sla-risk', {
      method: 'POST',
      body: JSON.stringify(caseData),
    });
  }

  // AI Advisory API
  async getAIAdvisory(processId = 'ONBOARD_V1') {
    return this.request(`/ai/advisory?process_id=${processId}`);
  }

  // Auth APIs
  async login(email, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.access_token);
    return data;
  }
}

export const api = new ApiClient();
