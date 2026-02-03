import { defineStore } from 'pinia';
import api from '../services/api';

export const useOperadorasStore = defineStore('operadoras', {
  state: () => ({
    lista: [],
    total: 0,
    paginaAtual: 1,
    itensPorPagina: 10,
    filtroBusca: '',
    loading: false,
    erro: null,
    erroStatus: null, // <--- 1. ADICIONADO: Necessário para o tratamento de erros (404, 500)
    operadoraAtual: null,
    historicoDespesas: [],
  }),

  getters: {
    totalPaginas: (state) => {
      // Evita divisão por zero
      if (state.itensPorPagina === 0) return 1;
      // Arredonda para cima (ex: 101 itens / 10 = 10.1 -> 11 páginas)
      return Math.ceil(state.total / state.itensPorPagina);
    }
  },

  actions: {
    async buscarOperadoras() {
      this.loading = true;
      this.erro = null;
      this.erroStatus = null; // Limpa o status de erro anterior

      try {
        const params = {
          page: this.paginaAtual,
          limit: this.itensPorPagina,
        };

        if (this.filtroBusca) {
          params.search = this.filtroBusca;
        }

        const response = await api.get('/operadoras', { params });

        // --- 2. CORREÇÃO DA PAGINAÇÃO ---
        // Seu backend retorna: { data: [...], meta: { total: 100, ... } }
        if (response.data && Array.isArray(response.data.data)) {
            this.lista = response.data.data;
            // Acessa o total dentro do objeto 'meta'
            this.total = response.data.meta ? response.data.meta.total : response.data.data.length;
        } else {
            // Fallback para caso a API mude e retorne lista direta
            this.lista = response.data;
            this.total = response.data.length;
            // (Removida a chamada recursiva incorreta que estava aqui)
        }

      } catch (error) {
        console.error("Erro na requisição:", error);

        if (error.response) {
            // Captura o status (404, 500, etc) para usar no frontend
            this.erroStatus = error.response.status;
            this.erro = error.response.data.detail || "Erro no servidor";
        } else if (error.request) {
            this.erro = "Sem resposta do servidor. Verifique sua conexão.";
        } else {
            this.erro = "Erro ao configurar a requisição.";
        }
      } finally {
        this.loading = false;
      }
    },

    async carregarDetalhesOperadora(cnpj) {
      this.loading = true;
      this.erro = null;
      this.operadoraAtual = null;
      this.historicoDespesas = [];

      try {
        const [resDados, resDespesas] = await Promise.all([
          api.get(`/operadoras/${cnpj}`),
          api.get(`/operadoras/${cnpj}/despesas`)
        ]);

        this.operadoraAtual = resDados.data;
        this.historicoDespesas = resDespesas.data;

      } catch (error) {
        console.error("Erro ao carregar detalhes:", error);
        // Também aplicamos a lógica de status aqui para consistência
        if (error.response) {
            this.erroStatus = error.response.status;
            this.erro = "Não foi possível carregar os detalhes desta operadora.";
        } else {
            this.erro = "Erro de conexão ao buscar detalhes.";
        }
      } finally {
        this.loading = false;
      }
    }
  }
});