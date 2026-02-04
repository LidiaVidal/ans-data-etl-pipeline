import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

import OperadoraDetalhe from '../views/OperadoraDetalhe.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/operadora/:cnpj',
      name: 'detalhes',
      component: OperadoraDetalhe 
    }
  ]
})

export default router