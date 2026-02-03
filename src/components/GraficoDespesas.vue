<template>
  <div class="grafico-container">
    <Bar v-if="chartData.labels.length > 0" :data="chartData" :options="chartOptions" />
    <p v-else>Carregando gráfico...</p>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Bar } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';

// Registra os componentes necessários do Chart.js
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

// Recebe os dados brutos da HomeView (ex: [{uf: 'SP', total: 100}, ...])
const props = defineProps({
  dados: {
    type: Array,
    required: true,
    default: () => []
  }
});

// Transforma os dados da API no formato que o Chart.js entende
const chartData = computed(() => {

  console.log("Dados recebidos no Gráfico:", props.dados);
  return {
    labels: props.dados.map(item => item.uf), // Eixo X: UFs
    datasets: [
      {
        label: 'Total de Despesas (R$)',
        backgroundColor: '#42b983',
        data: props.dados.map(item => item.valor_total || item.total || 0)
      }
    ]
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false
};
</script>

<style scoped>
.grafico-container {
  height: 400px; /* Importante para o gráfico não ficar gigante */
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
</style>