// Tipos de usuário e autenticação
export interface User {
  id: number;
  username: string;
  email: string;
  name?: string;
  is_staff: boolean;
  is_admin?: boolean;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Tipos para conexões de banco de dados
export interface Connection {
  id: number;
  name: string;
  database: string;
  host: string;
  user: string;
  password?: string; // Não deve ser retornado pela API
  type?: 'sqlite' | 'postgresql' | 'sqlserver' | 'oracle' | 'mysql';
  sgbd?: string; // Campo que pode vir do backend
}

export interface ConnectionTest {
  success: boolean;
  message: string;
  connection_time?: number;
}

// Tipos para parâmetros de consultas
export interface Parameter {
  id: number;
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean';
  allow_null: boolean;
  default_value?: string;
  allow_multiple_values: boolean;
}

// Tipos para consultas SQL
export interface Query {
  id: number;
  name: string;
  query: string;
  connection_id: number;
  connection?: Connection;
  connection_name?: string; // Nome da conexão vindo do backend
  parameters: Parameter[];
  timeout?: number;
  cache_duration?: number;
  created_by?: number;
  created_by_name?: string;
  created_at?: string;
  updated_at?: string;
  is_active?: boolean;
}

export interface QueryExecution {
  query_id: number;
  parameters?: Record<string, any>;
  limit?: number;
  offset?: number;
}

export interface QueryResult {
  columns: string[];
  rows: any[][];
  total_records: number;
  execution_time: number;
}

// Tipos para nós de projetos (árvore hierárquica)
export interface ProjectNode {
  id: number;
  name: string;
  parent_id?: number;
  query_id?: number;
  connection_id?: number;
  children: ProjectNode[];
  query?: Query;
}

// Tipos para projetos
export interface Project {
  id: number;
  name: string;
  description?: string;
  first_node_id?: number;
  root_node?: ProjectNode;
  node_count?: number;
  query_count?: number;
  created_by?: number;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
  is_active?: boolean;
}

export interface ProjectForm {
  name: string;
  description?: string;
}

export interface ProjectTree {
  id: number;
  name: string;
  description?: string;
  tree: ProjectNode[];
}

// Tipos para resposta de API genérica
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

// Tipos para paginação
export interface PaginatedResponse<T = any> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Tipos para formulários
export interface LoginForm {
  username: string;
  password: string;
}

export interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

// Tipos para navegação
export interface NavigationItem {
  title: string;
  path: string;
  icon?: string;
  children?: NavigationItem[];
  roles?: string[];
}
