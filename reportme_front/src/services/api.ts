import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  Project, 
  ProjectForm, 
  ProjectNode, 
  Connection, 
  Query, 
  Parameter,
  PaginatedResponse 
} from '../types';

// Configuração base da API
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Instância do Axios
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token JWT às requisições
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    console.log('🔑 Token no interceptor:', token ? 'EXISTS' : 'NOT_FOUND');
    console.log('🌐 Fazendo requisição para:', config.url);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('❌ Erro no interceptor de request:', error);
    return Promise.reject(error);
  }
);

// Interceptor para tratar respostas e refresh token
api.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log('✅ Resposta da API:', response.status, response.config.url);
    return response;
  },
  async (error) => {
    console.error('❌ Erro na resposta da API:', error.response?.status, error.config?.url);
    const originalRequest = error.config;
    
    // Melhor tratamento de erros de rede
    if (!error.response) {
      // Erro de rede (servidor não alcançável)
      if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
        error.isNetworkError = true;
        error.message = 'Servidor não foi alcançado. Verifique sua conexão ou se o servidor está funcionando.';
      } else if (error.code === 'ECONNREFUSED') {
        error.isNetworkError = true;
        error.message = 'Conexão recusada. Verifique se o servidor está rodando.';
      } else if (error.request) {
        error.isNetworkError = true;
        error.message = 'Não foi possível conectar ao servidor. Verifique sua conexão de internet.';
      }
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          // Retry a requisição original
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Token de refresh inválido, fazer logout
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Tipos para as respostas da API
export interface LoginResponse {
  access: string;
  refresh: string;
}

export interface UserProfile {
  user_id: number;
  username: string;
  email: string;
  is_staff: boolean;
}

export interface HealthCheck {
  status: string;
  message: string;
  version: string;
  timestamp: string;
}

// Serviços de autenticação
export const authService = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const response = await api.post('/auth/login/', { username, password });
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  getProfile: async (): Promise<UserProfile> => {
    const response = await api.get('/auth/profile/');
    return response.data;
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('access_token');
  },
};

// Serviços do core
export const coreService = {
  healthCheck: async (): Promise<HealthCheck> => {
    const response = await api.get('/core/health/');
    return response.data;
  },
};

// Serviços para Projetos
export const projectService = {
  getAll: async (): Promise<PaginatedResponse<Project>> => {
    const response = await api.get('/core/projects/');
    return response.data;
  },

  getById: async (id: number): Promise<Project> => {
    const response = await api.get(`/core/projects/${id}/`);
    return response.data;
  },

  create: async (data: ProjectForm): Promise<Project> => {
    const response = await api.post('/core/projects/', data);
    return response.data;
  },

  update: async (id: number, data: ProjectForm): Promise<Project> => {
    const response = await api.put(`/core/projects/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/core/projects/${id}/`);
  },

  getTree: async (id: number): Promise<ProjectNode[]> => {
    const response = await api.get(`/core/projects/${id}/tree/`);
    return response.data.tree || [];
  },
};

// Serviços para Project Nodes
export const projectNodeService = {
  getAll: async (projectId?: number): Promise<PaginatedResponse<ProjectNode>> => {
    const url = projectId ? `/core/project-nodes/?project=${projectId}` : '/core/project-nodes/';
    const response = await api.get(url);
    return response.data;
  },

  getById: async (id: number): Promise<ProjectNode> => {
    const response = await api.get(`/core/project-nodes/${id}/`);
    return response.data;
  },

  create: async (data: Partial<ProjectNode>): Promise<ProjectNode> => {
    const response = await api.post('/core/project-nodes/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<ProjectNode>): Promise<ProjectNode> => {
    const response = await api.put(`/core/project-nodes/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/core/project-nodes/${id}/`);
  },

  move: async (id: number, newParentId?: number): Promise<ProjectNode> => {
    const response = await api.patch(`/core/project-nodes/${id}/move/`, {
      parent_id: newParentId
    });
    return response.data;
  },
};

// Serviços para Conexões
export const connectionService = {
  getAll: async (): Promise<PaginatedResponse<Connection>> => {
    const response = await api.get('/core/connections/');
    return response.data;
  },

  getById: async (id: number): Promise<Connection> => {
    const response = await api.get(`/core/connections/${id}/`);
    return response.data;
  },

  create: async (data: Partial<Connection>): Promise<Connection> => {
    const response = await api.post('/core/connections/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Connection>): Promise<Connection> => {
    const response = await api.put(`/core/connections/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/core/connections/${id}/`);
  },

  test: async (id: number): Promise<any> => {
    const response = await api.post(`/core/connections/${id}/test/`);
    return response.data;
  },
};

// Serviços para Queries
export const queryService = {
  getAll: async (): Promise<PaginatedResponse<Query>> => {
    const response = await api.get('/core/queries/');
    return response.data;
  },

  getById: async (id: number): Promise<Query> => {
    const response = await api.get(`/core/queries/${id}/`);
    return response.data;
  },

  create: async (data: Partial<Query>): Promise<Query> => {
    const response = await api.post('/core/queries/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Query>): Promise<Query> => {
    const response = await api.put(`/core/queries/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/core/queries/${id}/`);
  },

  execute: async (id: number, parameters?: Record<string, any>): Promise<any> => {
    const response = await api.post('/core/queries/execute/', { 
      query_id: id, 
      parameters: parameters || {},
      limit: 100
    });
    return response.data;
  },
  
  testExecute: async (id: number): Promise<any> => {
    const response = await api.post('/core/queries/test-execute/', { 
      query_id: id, 
      parameters: {},
      limit: 100
    });
    return response.data;
  },

  validate: async (query: string, connection_id: number): Promise<any> => {
    const response = await api.post('/core/queries/validate/', { 
      query, 
      connection_id 
    });
    return response.data;
  },

  extractParameters: async (sql: string, query_id: number): Promise<any> => {
    const response = await api.post('/core/parameters/extract-from-sql/', { 
      sql, 
      query_id 
    });
    return response.data;
  },

  duplicate: async (id: number): Promise<Query> => {
    const response = await api.post(`/core/queries/${id}/duplicate/`);
    return response.data;
  },
};

// Serviços para Parâmetros
export const parameterService = {
  getAll: async (query_id?: number): Promise<PaginatedResponse<Parameter>> => {
    const params = query_id ? { query_id } : {};
    const response = await api.get('/core/parameters/', { params });
    return response.data;
  },

  getById: async (id: number): Promise<Parameter> => {
    const response = await api.get(`/core/parameters/${id}/`);
    return response.data;
  },

  create: async (data: Partial<Parameter>): Promise<Parameter> => {
    const response = await api.post('/core/parameters/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Parameter>): Promise<Parameter> => {
    const response = await api.put(`/core/parameters/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/core/parameters/${id}/`);
  },
};

export default api;
