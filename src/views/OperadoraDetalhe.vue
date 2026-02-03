<template>
  <div class="container">
    <button @click="$router.back()" class="btn-voltar">← Voltar</button>

    <div v-if="store.loading" class="feedback">Carregando detalhes...</div>
    <div v-if="store.erro" class="error">{{ store.erro }}</div>

    <div v-if="store.operadoraAtual && !store.loading">
      <div class="card-detalhe">
        <h1>{{ store.operadoraAtual.RazaoSocial}}</h1>
        <div class="grid-info">
          <p><strong>CNPJ:</strong> {{ store.operadoraAtual.CNPJ }}</p>
          <p><strong>Registro ANS:</strong> {{ store.operadoraAtual.RegistroANS }}</p>
          <p><strong>UF:</strong> {{ store.operadoraAtual.UF }}</p>
          <p><strong>Modalidade:</strong> {{ store.operadoraAtual.Modalidade }}</p>
        </div>
      </div>

      <h2>Histórico de Despesas</h2>
      
      <table v-if="store.historicoDespesas.length > 0" class="tabela-despesas">
        <thead>
          <tr>
            <th>Ano</th>
            <th>Trimestre</th>
            <th>Valor (R$)</th>
            <th>Data Processamento</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="desp in store.historicoDespesas" :key="desp.id">
            <td>{{ desp.ano }}</td>
            <td>{{ desp.trimestre }}º</td>
            <td>{{ formatarMoeda(desp.valor) }}</td> 
            <td>{{ desp.data_evento }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="feedback">Nenhum registro de despesa encontrado para o período.</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRoute } from 'vue-router'; // Para pegar o CNPJ da URL
import { useOperadorasStore } from '../stores/operadorasStore';

const store = useOperadorasStore();
const route = useRoute();

// Função auxiliar simples para moeda (Praticidade/KISS)
const formatarMoeda = (valor) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
};

onMounted(() => {
  // Pega o parâmetro :cnpj definido no router
  const cnpj = route.params.cnpj; 
  store.carregarDetalhesOperadora(cnpj);
});
</script>

<style scoped>
/* Adicione seu CSS aqui. Dica: Reuse as classes do HomeView se possível */
.card-detalhe { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
.tabela-despesas { width: 100%; border-collapse: collapse; }
.tabela-despesas th, .tabela-despesas td { border: 1px solid #ddd; padding: 8px; text-align: left; }
.btn-voltar { margin-bottom: 15px; cursor: pointer; background: none; border: 1px solid #ccc; padding: 5px 10px; border-radius: 4px;}
</style>