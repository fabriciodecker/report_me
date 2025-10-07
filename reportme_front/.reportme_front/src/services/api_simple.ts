import axios, { AxiosInstance } from 'axios';

// Configuração base da API
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Instância do Axios
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Serviços para Projetos (versão simplificada para teste)
export const projectService = {
  getAll: async () => {
    try {
      const response = await api.get('/core/projects/');
      return response.data || { results: [] };
    } catch (error) {
      console.error('Erro ao buscar projetos:', error);
      return { results: [] };
    }
  },
  create: async (data: any) => {
    try {
      const response = await api.post('/core/projects/', data);
      return response.data;
    } catch (error) {
      console.error('Erro ao criar projeto:', error);
      throw error;
    }
  },
  update: async (id: number, data: any) => {
    try {
      const response = await api.put(`/core/projects/${id}/`, data);
      return response.data;
    } catch (error) {
      console.error('Erro ao atualizar projeto:', error);
      throw error;
    }
  },
  delete: async (id: number) => {
    try {
      await api.delete(`/core/projects/${id}/`);
      return true;
    } catch (error) {
      console.error('Erro ao deletar projeto:', error);
      throw error;
    }
  },
  getTree: async (projectId: number) => {
    try {
      const response = await api.get(`/core/projects/${projectId}/tree/`);
      return response.data || [];
    } catch (error) {
      console.error('Erro ao buscar árvore do projeto:', error);
      return [];
    }
  },
};

// Serviços para Conexões (versão simplificada para teste)
export const connectionService = {
  getAll: async () => {
    try {
      const response = await api.get('/core/connections/');
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar conexões:', error);
      return [];
    }
  },
};

// Serviços para Queries (versão simplificada para teste)
export const queryService = {
  getAll: async () => {
    try {
      const response = await api.get('/core/queries/');
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar queries:', error);
      return [];
    }
  },
};

// Serviços de Auth (versão simplificada para teste)
export const authService = {
  login: async () => {
    // Mock para teste
    return { user: { name: 'Usuário Teste' } };
  },
  logout: async () => {
    // Mock para teste
    return true;
  },
  getProfile: async () => {
    // Mock para teste
    return { name: 'Usuário Teste', email: 'teste@example.com' };
  },
};

// Serviços para ProjectNode (versão simplificada para teste)
export const projectNodeService = {
  create: async (data: any) => {
    try {
      const response = await api.post('/core/project-nodes/', data);
      return response.data;
    } catch (error) {
      console.error('Erro ao criar nó do projeto:', error);
      throw error;
    }
  },
  update: async (id: number, data: any) => {
    try {
      const response = await api.put(`/core/project-nodes/${id}/`, data);
      return response.data;
    } catch (error) {
      console.error('Erro ao atualizar nó do projeto:', error);
      throw error;
    }
  },
  delete: async (id: number) => {
    try {
      await api.delete(`/core/project-nodes/${id}/`);
      return true;
    } catch (error) {
      console.error('Erro ao deletar nó do projeto:', error);
      throw error;
    }
  },
};
