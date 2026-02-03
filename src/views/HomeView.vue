<template>
  <div class="container">
    <h1>Lista de Operadoras</h1>

    <div class="search-bar">
      <input 
        v-model="store.filtroBusca" 
        placeholder="Buscar por Razão Social..." 
        @keyup.enter="buscar"
      />
      <button @click="buscar">Pesquisar</button>
    </div>

    <div v-if="store.loading" class="feedback">Carregando dados...</div>
    <div v-if="store.erro" class="error">{{ store.erro }}</div>

    <div v-if="!store.loading && !store.erro">
      <table class="operadoras-table">
        <thead>
          <tr>
            <th>Registro ANS</th>
            <th>CNPJ</th>
            <th>Razão Social</th>
            <th>Modalidade</th>
            <th>UF</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="op in store.lista" :key="op.CNPJ">
            <td>{{ op.RegistroANS }}</td>
            <td>{{ op.CNPJ }}</td>
            <td>{{ op.RazaoSocial }}</td>
            <td>{{ op.Modalidade }}</td>
            <td>{{ op.UF }}</td>
            <td>
              <router-link :to="`/operadora/${op.CNPJ}`" class="btn-detalhes">
                Ver Detalhes
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>

      <p v-if="store.lista.length === 0" class="feedback">Nenhuma operadora encontrada.</p>
    </div>

    <div class="pagination" v-if="store.total > 0">
      <button 
        :disabled="store.paginaAtual === 1" 
        @click="mudarPagina(-1)"
      >
        Anterior
      </button>
      
      <span>Página {{ store.paginaAtual }}</span>
      
      <button 
        :disabled="store.lista.length < store.itensPorPagina" 
        @click="mudarPagina(1)"
      >
        Próximo
      </button>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useOperadorasStore } from '../stores/operadorasStore';

// Inicializa o store
const store = useOperadorasStore();

// Função para acionar a busca (reseta para página 1)
const buscar = () => {
  store.paginaAtual = 1; // Sempre volta para a primeira página ao filtrar
  store.buscarOperadoras();
};

// Função para paginação
const mudarPagina = (delta) => {
  store.paginaAtual += delta;
  store.buscarOperadoras();
};

// onMounted é um "gancho" que roda assim que a tela abre
onMounted(() => {
  store.buscarOperadoras(); // Carrega os dados iniciais
});
</script>

<style scoped>
/* Estilos básicos para não ficar tudo branco */
.container { max-width: 1000px; margin: 0 auto; padding: 20px; }
.search-bar { margin-bottom: 20px; display: flex; gap: 10px; }
input { padding: 8px; flex: 1; border: 1px solid #ccc; border-radius: 4px; }
button { padding: 8px 16px; background-color: #42b983; color: white; border: none; cursor: pointer; border-radius: 4px; }
button:disabled { background-color: #ccc; cursor: not-allowed; }
.operadoras-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
.operadoras-table th, .operadoras-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
.operadoras-table th { background-color: #f2f2f2; }
.pagination { display: flex; justify-content: center; align-items: center; gap: 15px; margin-top: 20px; }
.error { color: red; background: #fee; padding: 10px; border-radius: 4px; }
.feedback { text-align: center; color: #666; margin: 20px 0; }
.btn-detalhes { color: #42b983; text-decoration: none; font-weight: bold; }
</style>