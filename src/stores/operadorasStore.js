import { defineStore } from 'pinia';
import api from '../services/api';

export const useOperadorasStore = defineStore('operadoras', {
  state: () => ({
    lista: [],          // Dados das operadoras
    total: 0,           // Total de registros no banco (para calcular número de páginas)
    paginaAtual: 1,
    itensPorPagina: 10, // ADICIONEI ISSO: O backend precisa saber quantos itens trazer
    filtroBusca: '',    // O termo pesquisado
    loading: false,
    erro: null,
    operadoraAtual: null,     
    historicoDespesas: [],
  }),

  actions: {
    async buscarOperadoras() {
      this.loading = true;
      this.erro = null;
      
      try {
        // 1. Preparamos os parâmetros para enviar na URL
        // O Axios transforma isso em: ?page=1&limit=10&search= termo
        const params = {
          page: this.paginaAtual,
          limit: this.itensPorPagina,
        };

        // Só enviamos o parâmetro de busca se o usuário tiver digitado algo
        if (this.filtroBusca) {
          params.search = this.filtroBusca;
        }

        // 2. Chamada à API (Conforme requisito GET /api/operadoras [cite: 143])
        const response = await api.get('/operadoras', { params });

        // 3. Atualização do Estado
        // ATENÇÃO: Aqui assumimos que seu Python retorna JSON no formato:
        // { data: [...], total: 100, page: 1, ... } (Opção B do doc )
        
        // Verifica se a resposta veio no formato esperado
        if (response.data && Array.isArray(response.data.data)) {
            this.lista = response.data.data; // A lista real
            this.total = response.data.total; // O número total para a paginação
        } else {
            // Fallback caso o backend retorne apenas a lista direta (sem paginação)
            this.lista = response.data;
            this.total = response.data.length;

            const response = await api.get('/operadoras/', { params }); 
        }

      } catch (error) {
        console.error("Erro na requisição:", error);
        
        // Tratamento de erro mais amigável
        if (error.response) {
            // O servidor respondeu com um status de erro (ex: 404, 500)
            this.erro = `Erro do servidor: ${error.response.status} - ${error.response.data.message || ''}`;
        } else if (error.request) {
            // A requisição foi feita mas não houve resposta (servidor fora do ar)
            this.erro = "Sem resposta do servidor. Verifique sua conexão ou se o Backend está rodando.";
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
      // Limpa dados anteriores para não mostrar "lixo" de outra navegação
      this.operadoraAtual = null; 
      this.historicoDespesas = [];

      try {
        // Trade-off Técnico: Promise.all vs Await sequencial
        // Optamos por Promise.all para disparar as duas requisições (dados + despesas)
        // simultaneamente. Isso reduz o tempo total de espera do usuário.
        const [resDados, resDespesas] = await Promise.all([
          api.get(`/operadoras/${cnpj}`),
          api.get(`/operadoras/${cnpj}/despesas`)
        ]);

        this.operadoraAtual = resDados.data;
        this.historicoDespesas = resDespesas.data;

      } catch (error) {
        console.error("Erro ao carregar detalhes:", error);
        this.erro = "Não foi possível carregar os detalhes desta operadora.";
      } finally {
        this.loading = false;
      }
    }


  }

  
});