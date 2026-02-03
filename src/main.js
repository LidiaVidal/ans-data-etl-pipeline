import { createApp } from 'vue'
import { createPinia } from 'pinia' // Importa o gerenciador de estado
import App from './App.vue'
import router from './router' // Importa o arquivo que criamos no Passo 2

const app = createApp(App)

// "Use" é como injetamos plugins no Vue
app.use(createPinia()) // Ativa o Pinia
app.use(router)        // Ativa o Router

app.mount('#app')