/**
 * Utilitário para padronizar o tratamento de erros da API
 */

export interface ApiError {
  message: string;
  type: 'network' | 'server' | 'validation' | 'authentication' | 'unknown';
  status?: number;
  details?: any;
}

/**
 * Converte erros do Axios em mensagens padronizadas para o usuário
 */
export const parseApiError = (error: any): ApiError => {
  // Erro de rede (servidor não alcançável)
  if (!error.response) {
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      return {
        message: 'Servidor não foi alcançado. Verifique sua conexão ou se o servidor está funcionando.',
        type: 'network'
      };
    }
    
    if (error.code === 'ECONNREFUSED') {
      return {
        message: 'Conexão recusada. Verifique se o servidor está rodando.',
        type: 'network'
      };
    }
    
    if (error.request) {
      return {
        message: 'Não foi possível conectar ao servidor. Verifique sua conexão de internet.',
        type: 'network'
      };
    }
  }

  const status = error.response?.status;
  const data = error.response?.data;

  switch (status) {
    case 400:
      return {
        message: data?.detail || 'Dados inválidos. Verifique as informações e tente novamente.',
        type: 'validation',
        status,
        details: data
      };

    case 401:
      return {
        message: data?.detail || 'Credenciais inválidas. Verifique usuário e senha.',
        type: 'authentication',
        status,
        details: data
      };

    case 403:
      return {
        message: data?.detail || 'Você não tem permissão para realizar esta ação.',
        type: 'authentication',
        status,
        details: data
      };

    case 404:
      return {
        message: data?.detail || 'Recurso não encontrado.',
        type: 'validation',
        status,
        details: data
      };

    case 500:
      return {
        message: 'Erro interno do servidor. Tente novamente mais tarde.',
        type: 'server',
        status,
        details: data
      };

    case 502:
    case 503:
    case 504:
      return {
        message: 'Servidor temporariamente indisponível. Tente novamente em alguns minutos.',
        type: 'server',
        status,
        details: data
      };

    default:
      return {
        message: data?.detail || 'Erro inesperado. Tente novamente.',
        type: 'unknown',
        status,
        details: data
      };
  }
};

/**
 * Hook para exibir mensagens de erro de forma consistente
 */
export const getErrorMessage = (error: any): string => {
  const apiError = parseApiError(error);
  return apiError.message;
};

/**
 * Verifica se o erro é relacionado à rede/conectividade
 */
export const isNetworkError = (error: any): boolean => {
  const apiError = parseApiError(error);
  return apiError.type === 'network';
};

/**
 * Verifica se o erro é de autenticação
 */
export const isAuthError = (error: any): boolean => {
  const apiError = parseApiError(error);
  return apiError.type === 'authentication';
};

/**
 * Verifica se o erro é de validação
 */
export const isValidationError = (error: any): boolean => {
  const apiError = parseApiError(error);
  return apiError.type === 'validation';
};