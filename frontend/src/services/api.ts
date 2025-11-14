/**
 * API Service Layer
 *
 * Centralized API calls using axios
 */

import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response.data,
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  // Agent endpoints
  async listAgents() {
    return this.client.get('/api/agents/list');
  }

  async executeAgentTask(agentType: string, taskType: string, taskData: any) {
    return this.client.post('/api/agents/execute', {
      agent_type: agentType,
      task_type: taskType,
      task_data: taskData,
    });
  }

  async getAgentStatus(agentName: string) {
    return this.client.get(`/api/agents/${agentName}/status`);
  }

  async getAgentHistory(agentName: string, limit = 20, offset = 0) {
    return this.client.get(`/api/agents/${agentName}/history`, {
      params: { limit, offset },
    });
  }

  // Task endpoints
  async createTask(taskData: any) {
    return this.client.post('/api/tasks/create', taskData);
  }

  async getTask(taskId: string) {
    return this.client.get(`/api/tasks/${taskId}`);
  }

  async listTasks(filters?: any) {
    return this.client.get('/api/tasks/', { params: filters });
  }

  async deleteTask(taskId: string) {
    return this.client.delete(`/api/tasks/${taskId}`);
  }

  async getTaskStatistics(userId?: string) {
    return this.client.get('/api/tasks/stats/summary', {
      params: userId ? { user_id: userId } : {},
    });
  }

  // Workflow endpoints
  async executeWorkflow(workflowData: any) {
    return this.client.post('/api/workflows/execute', workflowData);
  }

  async getWorkflow(workflowId: string) {
    return this.client.get(`/api/workflows/${workflowId}`);
  }

  async listWorkflows(filters?: any) {
    return this.client.get('/api/workflows/', { params: filters });
  }

  async executeScenario(scenarioName: string, scenarioConfig: any) {
    return this.client.post(`/api/workflows/scenarios/${scenarioName}`, scenarioConfig);
  }

  // Monitoring endpoints
  async getHealth() {
    return this.client.get('/api/monitoring/health');
  }

  async getMetrics() {
    return this.client.get('/api/monitoring/metrics');
  }

  async getAgentMetrics(agentType: string) {
    return this.client.get(`/api/monitoring/metrics/agents/${agentType}`);
  }

  async getTimeseriesMetrics(params?: any) {
    return this.client.get('/api/monitoring/metrics/timeseries', { params });
  }

  async getDashboardData() {
    return this.client.get('/api/monitoring/dashboard');
  }

  async recordMetric(metricData: any) {
    return this.client.post('/api/monitoring/metrics/record', metricData);
  }
}

export default new ApiService();
